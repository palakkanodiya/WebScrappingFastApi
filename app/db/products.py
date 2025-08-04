import logging
from bson.objectid import ObjectId
from typing import Dict, Any, List, Optional
from .client import db
from .constants import PRODUCTS_COLLECTION, FIELD_NAME, FIELD_URL, FIELD_PRICE

logger = logging.getLogger(__name__)
products_coll = db[PRODUCTS_COLLECTION]

def save_product(product: Dict[str, Any]) -> None:
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
    try:
        return list(products_coll.find())
    except Exception:
        logger.exception("Failed to retrieve all products")
        return []
