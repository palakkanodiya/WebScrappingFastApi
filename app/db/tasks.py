import logging
from bson.objectid import ObjectId
from typing import Dict, Any, List, Optional
from .client import db
from .constants import TASKS_COLLECTION, FIELD_CLIENT

logger = logging.getLogger(__name__)
tasks_coll = db[TASKS_COLLECTION]

def create_task(task: Dict[str, Any]) -> str:
    if not task:
        raise ValueError("Task data is empty")
    try:
        res = tasks_coll.insert_one(task)
        logger.info(f"Task inserted with ID: {res.inserted_id}")
        return str(res.inserted_id)
    except Exception:
        logger.exception("Failed to create task")
        raise

def update_task(task_id: str, updates: Dict[str, Any]) -> None:
    if not updates:
        raise ValueError("Update data is empty")
    try:
        result = tasks_coll.update_one({"_id": ObjectId(task_id)}, {"$set": updates})
        if result.matched_count == 0:
            logger.warning(f"No task found with ID: {task_id}")
    except Exception:
        logger.exception(f"Failed to update task {task_id}")
        raise

def get_task_by_id(task_id: str) -> Optional[Dict[str, Any]]:
    try:
        return tasks_coll.find_one({"_id": ObjectId(task_id)})
    except Exception:
        logger.exception(f"Failed to fetch task {task_id}")
        return None

def get_tasks_by_client(client_name: str) -> List[Dict[str, Any]]:
    try:
        return list(tasks_coll.find({FIELD_CLIENT: client_name}))
    except Exception:
        logger.exception(f"Failed to fetch tasks for client: {client_name}")
        return []
