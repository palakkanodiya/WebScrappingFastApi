from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Body
from typing import List, Optional
from models import TaskCreate, Product, ProductSearch    # Added ProductSearch
import db
from scraper import scrap_url
from datetime import datetime

app = FastAPI()

# Root endpoint
@app.get("/")
def root():
    return {"message": "Welcome to the Walmart Scraping API"}

# Create a new scraping task
@app.post("/tasks", response_model=str, summary="Create a New Task")
def create_task(task: TaskCreate):
    task_data = task.dict()
    task_data["created_at"] = datetime.utcnow()
    task_data["status"] = "pending"
    task_id = db.create_task(task_data)
    return task_id


# Start scraping for a particular task
@app.post("/tasks/{task_id}/scrape", summary="Scrape Product Data")
def scrape_product_data(task_id: str, background_tasks: BackgroundTasks):
    task = db.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["status"] != "pending":
        raise HTTPException(status_code=400, detail="Task is not in pending state")

    # Background function handles status and DB updates
    def scrape_and_save(task):
        try:
            product = scrap_url(task["url"])
            product['client'] = task["client"]
            db.save_product(product)
            db.update_task(task_id, {
                "status": "success",
                "finished_at": datetime.utcnow(),
                "product_name": product.get("name"),
            })
        except Exception:
            db.update_task(task_id, {
                "status": "error",
                "finished_at": datetime.utcnow(),
            })

    background_tasks.add_task(scrape_and_save, task)
    return {"message": "Scraping started in the background"}


# Get all tasks for a client
@app.get("/tasks", summary="Get Tasks by Client")
def get_tasks_by_client(client: str = Query(..., description="Client identifier")): 
    tasks = db.get_tasks_by_client(client)
    if not tasks:
        raise HTTPException(status_code=404, detail="No tasks found for this client")
    for t in tasks:
        t["id"] = str(t["_id"])
        t.pop("_id", None)
    return tasks

# Get task by ID
@app.get("/tasks/{task_id}", summary="Get Task by ID")
def get_task(task_id: str):
    task = db.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task["id"] = str(task["_id"])
    task.pop("_id", None)
    return task

# Get all products
@app.get("/products", response_model=List[Product], summary="Get All Products")
def get_all_products():
    products = db.get_all_products()
    for p in products:
        p["id"] = str(p["_id"])
        p.pop("_id", None)
    return products

# Search products by filters
@app.get("/products/search", response_model=List[Product], summary="Search Products")
def search_products(
    name: Optional[str] = None,
    id: Optional[str] = None,
    price: Optional[str] = None
):
    search_params = ProductSearch(name=name, id=id, price=price)
    products = db.get_product(**search_params.dict(exclude_none=True))
    if not products:
        raise HTTPException(status_code=404, detail="No products found")
    for p in products:
        p["id"] = str(p["_id"])
        p.pop("_id", None)
    return products

# Update a client's own task
@app.patch("/tasks/{task_id}", summary="Update Your Own Task ONLY")
def update_task(
    task_id: str,
    client: str = Query(..., description="Client identifier"),
    updates: dict = Body(..., description="Fields to update")
):
    task = db.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["client"] != client:
        raise HTTPException(status_code=403, detail="Permission denied; not your task")
    db.update_task(task_id, updates)
    return {"updated": True}
