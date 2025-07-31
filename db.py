
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from typing import List, Optional, Dict, Any

load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = os.environ.get("MONGO_DB", "walmart_scraped")
TASKS_COLLECTION = os.environ.get("TASKS_COLLECTION", "tasks")
PRODUCTS_COLLECTION = os.environ.get("PRODUCTS_COLLECTION", "products")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
tasks_coll = db[TASKS_COLLECTION]
products_coll = db[PRODUCTS_COLLECTION]

def create_task(task: Dict[str, Any]) -> str:
    res = tasks_coll.insert_one(task)
    return str(res.inserted_id)

def update_task(task_id: str, updates: Dict[str, Any]) -> None:
    tasks_coll.update_one({"_id": ObjectId(task_id)}, {"$set": updates})

def get_task_by_id(task_id: str) -> Optional[Dict[str, Any]]:
    return tasks_coll.find_one({"_id": ObjectId(task_id)})

def get_tasks_by_client(client_name: str) -> List[Dict[str, Any]]:
    return list(tasks_coll.find({"client": client_name}))

def save_product(product: Dict[str, Any]) -> None:
    filter_query = {"name": product["name"], "url": product["url"]}
    update_data = {"$set": product}
    products_coll.update_one(filter_query, update_data, upsert=True)

def get_product(**kwargs) -> Optional[Any]:
    if 'id' in kwargs:
        return products_coll.find_one({"_id": ObjectId(kwargs['id'])})
    if 'name' in kwargs:
        return list(products_coll.find({"name": kwargs['name']}))
    if 'price' in kwargs:
        return list(products_coll.find({"price": kwargs['price']}))
    return []

def get_all_products() -> List[Dict[str, Any]]:
    return list(products_coll.find())
