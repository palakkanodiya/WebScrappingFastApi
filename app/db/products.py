import logging
from bson.objectid import ObjectId
from typing import Dict, Any, List, Union
from .client import db
from .constants import PRODUCTS_COLLECTION, FIELD_NAME, FIELD_URL, FIELD_PRICE


class ProductError(Exception):
    """Base exception for all product-related errors."""
    pass

class ProductDataEmptyError(ProductError):
    """Raised when product data is empty."""
    def __init__(self, message="Product data is empty."):
        super().__init__(message)

class ProductMissingFieldsError(ProductError):
    """Raised when required product fields are missing."""
    def __init__(self, message="Product must contain both 'name' and 'url'."):
        super().__init__(message)

class ProductNotFoundError(ProductError):
    """Raised when a product is not found in the database."""
    def __init__(self, message="Requested product not found."):
        super().__init__(message)

class DatabaseError(ProductError):
    """Raised for database-related issues."""
    def __init__(self, message="A database error occurred."):
        super().__init__(message)


logger = logging.getLogger(__name__)
products_coll = db[PRODUCTS_COLLECTION]


def save_product(product: Dict[str, Any]) -> None:
    """
    Inserts or updates a product document in the database using 'name' and 'url' as identifiers.

    Raises
    ------
    ProductDataEmptyError: If product dict is empty.
    ProductMissingFieldsError: If required fields are missing.
    DatabaseError: If DB operation fails.
    """
    if not product:
        raise ProductDataEmptyError()

    if FIELD_NAME not in product or FIELD_URL not in product:
        raise ProductMissingFieldsError()

    try:
        filter_query = {FIELD_NAME: product[FIELD_NAME], FIELD_URL: product[FIELD_URL]}
        update_data = {"$set": product}
        result = products_coll.update_one(filter_query, update_data, upsert=True)

        logger.info(
            f"Product saved (Matched: {result.matched_count}, Modified: {result.modified_count})"
        )
    except Exception as e:
        logger.exception("Error saving product to DB.")
        raise DatabaseError(str(e))


def get_product(**filters) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Retrieves one or more products using filter keys: 'id', 'name', or 'price'.

    Raises
    ------
    ProductNotFoundError: If no product matches the filter.
    DatabaseError: If DB query fails.
    """
    try:
        if "id" in filters:
            result = products_coll.find_one({"_id": ObjectId(filters["id"])})
            if not result:
                raise ProductNotFoundError(f"No product found with ID: {filters['id']}")
            return result

        if FIELD_NAME in filters:
            results = list(products_coll.find({FIELD_NAME: filters[FIELD_NAME]}))
            if not results:
                raise ProductNotFoundError(f"No products found with name: {filters[FIELD_NAME]}")
            return results

        if FIELD_PRICE in filters:
            results = list(products_coll.find({FIELD_PRICE: filters[FIELD_PRICE]}))
            if not results:
                raise ProductNotFoundError(f"No products found with price: {filters[FIELD_PRICE]}")
            return results

        raise ProductNotFoundError("No valid filter provided to find product.")

    except ProductNotFoundError:
        raise
    except Exception as e:
        logger.exception("Error retrieving product(s).")
        raise DatabaseError(str(e))


def get_all_products() -> List[Dict[str, Any]]:
    """
    Fetches all products from the database.

    Raises
    ------
    DatabaseError: If DB query fails.
    """
    try:
        return list(products_coll.find())
    except Exception as e:
        logger.exception("Error fetching all products.")
        raise DatabaseError(f"Error retrieving all products: {str(e)}")
