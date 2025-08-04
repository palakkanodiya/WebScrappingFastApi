from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Body
from typing import List, Optional
from app.models.schema import TaskCreate, Product, ProductSearch
from app.db import tasks as task_db
from app.db import products as product_db
from app.services.scraper import scrap_url
from datetime import datetime
import logging

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Walmart Web Scraping API", version="1.0")


@app.get("/", summary="Root Endpoint", tags=["Root"])
def root():
    """
    Root endpoint for health check or welcome message.

    Returns:
        A welcome message indicating that the API is operational.
    """
    logger.info("Root endpoint hit")
    return {"message": "Welcome to the Walmart Scraping API"}


@app.post("/tasks", response_model=str, summary="Create a New Task", tags=["Tasks"])
def create_task(task: TaskCreate):
    """
    Create a new scraping task.

    Args:
        task (TaskCreate): Task details including URL and client ID.

    Returns:
        str: The ID of the newly created task.
    """
    try:
        task_data = task.dict()
        task_data["created_at"] = datetime.utcnow()
        task_data["status"] = "pending"
        task_id = task_db.create_task(task_data)
        logger.info(f"Task created successfully with ID: {task_id}")
        return task_id
    except Exception as e:
        logger.exception("Failed to create task")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@app.post("/tasks/{task_id}/scrape", summary="Scrape Product Data", tags=["Tasks"])
def scrape_product_data(task_id: str, background_tasks: BackgroundTasks):
    """
    Trigger background scraping for a specific task ID.

    Args:
        task_id (str): The ID of the task to scrape.
        background_tasks (BackgroundTasks): FastAPI background task handler.

    Returns:
        dict: A message confirming background scraping has started.
    """
    task = task_db.get_task_by_id(task_id)
    if not task:
        logger.warning(f"Task with ID {task_id} not found")
        raise HTTPException(status_code=404, detail="Task not found")
    if task["status"] != "pending":
        logger.warning(f"Task {task_id} is not in pending state")
        raise HTTPException(status_code=400, detail="Task is not in pending state")

    def scrape_and_save(task):
        try:
            logger.info(f"Started scraping for task ID: {task['_id']}")
            product = scrap_url(task["url"])
            product["client"] = task["client"]
            product_db.save_product(product)
            task_db.update_task(task_id, {
                "status": "success",
                "finished_at": datetime.utcnow(),
                "product_name": product.get("name"),
            })
            logger.info(f"Successfully scraped and saved product for task ID: {task['_id']}")
        except Exception as e:
            logger.exception(f"Error scraping task ID {task['_id']}")
            task_db.update_task(task_id, {
                "status": "error",
                "error_message": str(e),
                "finished_at": datetime.utcnow()
            })

    background_tasks.add_task(scrape_and_save, task)
    logger.info(f"Scraping task {task_id} added to background")
    return {"message": "Scraping started in the background"}


@app.get("/tasks", summary="Get Tasks by Client", tags=["Tasks"])
def get_tasks_by_client(client: str = Query(..., description="Client identifier")):
    """
    Retrieve all tasks created by a specific client.

    Args:
        client (str): Client identifier.

    Returns:
        List[dict]: A list of tasks created by the client.
    """
    try:
        tasks = task_db.get_tasks_by_client(client)
        if not tasks:
            logger.warning(f"No tasks found for client: {client}")
            raise HTTPException(status_code=404, detail="No tasks found for this client")
        for task in tasks:
            task["id"] = str(task.pop("_id", ""))
        logger.info(f"Retrieved {len(tasks)} tasks for client: {client}")
        return tasks
    except Exception as e:
        logger.exception(f"Error retrieving tasks for client {client}")
        raise HTTPException(status_code=500, detail=f"Error retrieving tasks: {str(e)}")


@app.get("/tasks/{task_id}", summary="Get Task by ID", tags=["Tasks"])
def get_task(task_id: str):
    """
    Retrieve a task by its ID.

    Args:
        task_id (str): The unique ID of the task.

    Returns:
        dict: Task data.
    """
    try:
        task = task_db.get_task_by_id(task_id)
        if not task:
            logger.warning(f"Task not found with ID: {task_id}")
            raise HTTPException(status_code=404, detail="Task not found")
        task["id"] = str(task.pop("_id", ""))
        logger.info(f"Retrieved task with ID: {task_id}")
        return task
    except Exception as e:
        logger.exception(f"Error retrieving task {task_id}")
        raise HTTPException(status_code=500, detail=f"Error retrieving task: {str(e)}")


@app.get("/products", response_model=List[Product], summary="Get All Products", tags=["Products"])
def get_all_products():
    """
    Retrieve all scraped product records.

    Returns:
        List[Product]: List of all products.
    """
    try:
        products = product_db.get_all_products()
        for product in products:
            product["id"] = str(product.pop("_id", ""))
        logger.info(f"Retrieved {len(products)} products")
        return products
    except Exception as e:
        logger.exception("Error retrieving products")
        raise HTTPException(status_code=500, detail=f"Error retrieving products: {str(e)}")


@app.get("/products/search", response_model=List[Product], summary="Search Products", tags=["Products"])
def search_products(
    name: Optional[str] = None,
    id: Optional[str] = None,
    price: Optional[str] = None
):
    """
    Search products based on name, ID, or price.

    Args:
        name (Optional[str]): Product name.
        id (Optional[str]): Product ID.
        price (Optional[str]): Product price.

    Returns:
        List[Product]: List of matching products.
    """
    try:
        search_params = ProductSearch(name=name, id=id, price=price)
        products = product_db.get_product(**search_params.dict(exclude_none=True))
        if not products:
            logger.warning("No products found for given search criteria")
            raise HTTPException(status_code=404, detail="No products found")
        for product in products:
            product["id"] = str(product.pop("_id", ""))
        logger.info(f"Found {len(products)} product(s) matching search criteria")
        return products

    except HTTPException as e:
        raise e  # Let FastAPI handle it

    except Exception as e:
        logger.exception("Unexpected error searching products")
        raise HTTPException(status_code=500, detail=f"Error searching products: {str(e)}")


@app.patch("/tasks/{task_id}", summary="Update Your Own Task ONLY", tags=["Tasks"])
def update_task(
    task_id: str,
    client: str = Query(..., description="Client identifier"),
    updates: dict = Body(..., description="Fields to update")
):
    """
    Update specific fields of a task, but only if the client is the owner.

    Args:
        task_id (str): Task ID to update.
        client (str): Client attempting the update.
        updates (dict): Dictionary of updates to apply.

    Returns:
        dict: Result of the update operation.
    """
    try:
        task = task_db.get_task_by_id(task_id)
        if not task:
            logger.warning(f"Task not found with ID: {task_id}")
            raise HTTPException(status_code=404, detail="Task not found")
        if task["client"] != client:
            logger.warning(f"Client '{client}' tried to modify task not owned by them: {task_id}")
            raise HTTPException(status_code=403, detail="Permission denied; not your task")
        task_db.update_task(task_id, updates)
        logger.info(f"Task {task_id} updated by client: {client}")
        return {"updated": True}
    except Exception as e:
        logger.exception(f"Error updating task {task_id}")
        raise HTTPException(status_code=500, detail=f"Error updating task: {str(e)}")
