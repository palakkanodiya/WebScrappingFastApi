from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Body
from app.models.schema import TaskCreate
from app.db import tasks as task_db
from app.db import products as product_db
from app.services.scraper import scrap_url
from app.exceptionns import (
    TaskNotFoundError, PermissionDeniedError, TaskStatusInvalidError, TaskCreationError
)
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=str, summary="Create a New Task")
def create_task(task: TaskCreate):
    """
    Create a new scraping task.

    Args:
        task (TaskCreate): The task object containing client and URL.

    Returns:
        str: ID of the created task.

    Raises:
        TaskCreationError: If task creation fails.
    """
    try:
        task_data = task.dict()
        task_data["created_at"] = datetime.utcnow()
        task_data["status"] = "pending"
        task_id = task_db.create_task(task_data)
        logger.info(f"Task created with ID: {task_id}")
        return task_id
    except Exception as e:
        logger.exception("Failed to create task")
        raise TaskCreationError(str(e))


@router.post("/{task_id}/scrape", summary="Scrape Product Data")
def scrape_product_data(task_id: str, background_tasks: BackgroundTasks):
    """
    Start scraping product data for a task in the background.

    Args:
        task_id (str): The ID of the task to execute.
        background_tasks (BackgroundTasks): FastAPI background task handler.

    Returns:
        dict: Message indicating scraping has started.

    Raises:
        TaskNotFoundError: If task does not exist.
        TaskStatusInvalidError: If task is not in 'pending' state.
    """
    task = task_db.get_task_by_id(task_id)
    if not task:
        raise TaskNotFoundError(task_id)
    if task["status"] != "pending":
        raise TaskStatusInvalidError(task_id)

    def scrape_and_save(task):
        """
        Scrapes product data and saves it to DB; updates task status accordingly.

        Args:
            task (dict): Task object from DB.
        """
        try:
            product = scrap_url(task["url"])
            product["client"] = task["client"]
            product_db.save_product(product)
            task_db.update_task(task["_id"], {
                "status": "success",
                "finished_at": datetime.utcnow(),
                "product_name": product.get("name"),
            })
        except Exception as e:
            task_db.update_task(task["_id"], {
                "status": "error",
                "error_message": str(e),
                "finished_at": datetime.utcnow()
            })
            logger.exception(f"Scraping failed for task: {task['_id']}")

    background_tasks.add_task(scrape_and_save, task)
    return {"message": "Scraping started in background"}


@router.get("", summary="Get Tasks by Client")
def get_tasks_by_client(client: str = Query(...)):
    """
    Get all tasks for a specific client.

    Args:
        client (str): The client identifier (query param).

    Returns:
        list: List of tasks belonging to the client.

    Raises:
        TaskNotFoundError: If no tasks found.
        HTTPException: If any other error occurs.
    """
    try:
        tasks = task_db.get_tasks_by_client(client)
        if not tasks:
            raise TaskNotFoundError(client)
        for task in tasks:
            task["id"] = str(task.pop("_id", ""))
        return tasks
    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error retrieving tasks")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}", summary="Get Task by ID")
def get_task(task_id: str):
    """
    Retrieve a specific task by its ID.

    Args:
        task_id (str): Task ID.

    Returns:
        dict: Task document.

    Raises:
        TaskNotFoundError: If task not found.
        HTTPException: For server errors.
    """
    try:
        task = task_db.get_task_by_id(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        task["id"] = str(task.pop("_id", ""))
        return task
    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Error fetching task")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{task_id}", summary="Update Your Own Task ONLY")
def update_task(
    task_id: str,
    client: str = Query(...),
    updates: dict = Body(...)
):
    """
    Update a task. Only the original client can update.

    Args:
        task_id (str): Task ID.
        client (str): Client identifier (used for permission check).
        updates (dict): Dictionary of fields to update.

    Returns:
        dict: { "updated": True }

    Raises:
        TaskNotFoundError: If task is not found.
        PermissionDeniedError: If client is not authorized.
        HTTPException: For server errors.
    """
    try:
        task = task_db.get_task_by_id(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        if task["client"] != client:
            raise PermissionDeniedError()
        task_db.update_task(task_id, updates)
        return {"updated": True}
    except (TaskNotFoundError, PermissionDeniedError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.exception("Update task failed")
        raise HTTPException(status_code=500, detail=str(e))
