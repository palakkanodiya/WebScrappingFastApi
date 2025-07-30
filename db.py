# db.py
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client["walmart_scraped"]
tasks_coll = db["tasks"]
products_coll = db["products"]

def create_task(task: dict):
    res = tasks_coll.insert_one(task)
    return str(res.inserted_id)

def update_task(task_id: str, updates: dict):
    tasks_coll.update_one({"_id": ObjectId(task_id)}, {"$set": updates})

def get_task_by_id(task_id: str):
    return tasks_coll.find_one({"_id": ObjectId(task_id)})

def get_tasks_by_client(client_name: str):
    return list(tasks_coll.find({"client": client_name}))

def save_product(product: dict):
    # Upsert product by (name, url)
    filter_query = {"name": product["name"], "url": product["url"]}
    update_data = {"$set": product}
    products_coll.update_one(filter_query, update_data, upsert=True)

def get_product(**kwargs):
    if 'id' in kwargs:
        return products_coll.find_one({"_id": ObjectId(kwargs['id'])})
    if 'name' in kwargs:
        return list(products_coll.find({"name": kwargs['name']}))
    if 'price' in kwargs:
        return list(products_coll.find({"price": kwargs['price']}))
    return []

def get_all_products():
    return list(products_coll.find())
