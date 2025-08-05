import logging
from bson.objectid import ObjectId
from typing import Dict, Any, List, Optional
from .client import db
from .constants import TASKS_COLLECTION, FIELD_CLIENT


class TaskError(Exception):
    """Base exception for task-related operations."""
    pass

class TaskDataEmptyError(TaskError):
    """Raised when provided task data is empty."""
    def __init__(self, message="Task data is empty."):
        super().__init__(message)

class TaskUpdateEmptyError(TaskError):
    """Raised when update data is empty."""
    def __init__(self, message="Update data cannot be empty."):
        super().__init__(message)

class TaskNotFoundError(TaskError):
    """Raised when a task is not found in the database."""
    def __init__(self, message="Task not found."):
        super().__init__(message)

class TaskDatabaseError(TaskError):
    """Raised when a database operation fails."""
    def __init__(self, message="Database error occurred during task operation."):
        super().__init__(message)



logger = logging.getLogger(__name__)
tasks_coll = db[TASKS_COLLECTION]


def create_task(task: Dict[str, Any]) -> str:
    """
    Inserts a new task document into the MongoDB collection.
    """
    if not task:
        raise TaskDataEmptyError()

    try:
        res = tasks_coll.insert_one(task)
        logger.info(f"Task inserted with ID: {res.inserted_id}")
        return str(res.inserted_id)
    except Exception as e:
        logger.exception("Failed to create task.")
        raise TaskDatabaseError(str(e))


def update_task(task_id: str, updates: Dict[str, Any]) -> None:
    """
    Updates an existing task document by its ObjectId.
    """
    if not updates:
        raise TaskUpdateEmptyError()

    try:
        result = tasks_coll.update_one({"_id": ObjectId(task_id)}, {"$set": updates})
        if result.matched_count == 0:
            logger.warning(f"No task found with ID: {task_id}")
            raise TaskNotFoundError(f"No task found with ID: {task_id}")
    except TaskNotFoundError:
        raise
    except Exception as e:
        logger.exception(f"Failed to update task {task_id}")
        raise TaskDatabaseError(str(e))


def get_task_by_id(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a task document by its ObjectId.
    """
    try:
        result = tasks_coll.find_one({"_id": ObjectId(task_id)})
        if not result:
            raise TaskNotFoundError(f"Task with ID {task_id} not found.")
        return result
    except TaskNotFoundError:
        raise
    except Exception as e:
        logger.exception(f"Failed to fetch task {task_id}")
        raise TaskDatabaseError(str(e))


def get_tasks_by_client(client_name: str) -> List[Dict[str, Any]]:
    """
    Retrieves all tasks associated with a specific client.
    """
    try:
        results = list(tasks_coll.find({FIELD_CLIENT: client_name}))
        if not results:
            raise TaskNotFoundError(f"No tasks found for client: {client_name}")
        return results
    except TaskNotFoundError:
        raise
    except Exception as e:
        logger.exception(f"Failed to fetch tasks for client: {client_name}")
        raise TaskDatabaseError(str(e))

