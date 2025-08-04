from fastapi import FastAPI
from app.routes import tasks, products
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Walmart Web Scraping API",
    version="1.0",
    description="API for scraping Walmart product data and managing scraping tasks."
)

@app.get("/", tags=["Root"])
def root():
    """
    Root health check endpoint.

    Returns:
        dict: Welcome message confirming the API is running.
    """
    logger.info("Root endpoint hit")
    return {"message": "Welcome to the Walmart Scraping API"}

# Register route modules
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(products.router, prefix="/products", tags=["Products"])
