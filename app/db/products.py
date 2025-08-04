import logging
from bson.objectid import ObjectId
from typing import Dict, Any, List, Optional
from .client import db
from .constants import PRODUCTS_COLLECTION, FIELD_NAME, FIELD_URL, FIELD_PRICE

logger = logging.getLogger(__name__)
products_coll = db[PRODUCTS_COLLECTION]


def save_product(product: Dict[str, Any]) -> None:
    """
    Inserts or updates a product document in the database using name and URL as identifiers.

    Parameters
    ----------
    product : dict
        Product data to be saved. Must contain 'name' and 'url' fields.

    Raises
    ------
    ValueError
        If the product data is empty.
    KeyError
        If 'name' or 'url' fields are missing.
    Exception
        If the database operation fails.
    """
    if not product:
        raise ValueError("Product data is empty")
    if FIELD_NAME not in product or FIELD_URL not in product:
        raise KeyError("Product must contain 'name' and 'url' fields")

    try:
        filter_query = {FIELD_NAME: product[FIELD_NAME], FIELD_URL: product[FIELD_URL]}
        update_data = {"$set": product}
        result = products_coll.update_one(filter_query, update_data, upsert=True)
        logger.info(f"Product saved. Matched: {result.matched_count}, Modified: {result.modified_count}")
    except Exception:
        logger.exception("Failed to save product")
        raise


def get_product(**kwargs) -> Optional[Any]:
    """
    Retrieves a product from the database using one of the optional filters.

    Parameters
    ----------
    kwargs : dict
        Accepts one of the following filters:
        - id (str): ObjectId of the product.
        - name (str): Name of the product.
        - price (Any): Price of the product.

    Returns
    -------
    dict or list or None
        - Single product dict if 'id' is used.
        - List of matching products if 'name' or 'price' is used.
        - Empty list or None if no match or error.
    """
    try:
        if 'id' in kwargs:
            return products_coll.find_one({"_id": ObjectId(kwargs['id'])})
        if FIELD_NAME in kwargs:
            return list(products_coll.find({FIELD_NAME: kwargs[FIELD_NAME]}))
        if FIELD_PRICE in kwargs:
            return list(products_coll.find({FIELD_PRICE: kwargs[FIELD_PRICE]}))
        return []
    except Exception:
        logger.exception("Failed to search product")
        return None


def get_all_products() -> List[Dict[str, Any]]:
    """
    Retrieves all product documents from the database.

    Returns
    -------
    list of dict
        List of all products. Returns empty list on error.
    """
    try:
        return list(products_coll.find())
    except Exception:
        logger.exception("Failed to retrieve all products")
        return []
