from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.models.schema import Product, ProductSearch
from app.db import products as product_db
from app.exceptionns import ProductNotFoundError
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=List[Product], summary="Get All Products")
def get_all_products():
    """
    Retrieve all scraped product entries from the database.

    Returns:
        List[Product]: A list of all products.

    Raises:
        HTTPException: If an error occurs during retrieval.
    """
    try:
        products = product_db.get_all_products()
        for product in products:
            product["id"] = str(product.pop("_id", ""))
        return products
    except Exception as e:
        logger.exception("Error fetching all products")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=List[Product], summary="Search Products")
def search_products(
    name: Optional[str] = None,
    id: Optional[str] = None,
    price: Optional[str] = None
):
    """
    Search for products using filters like name, id, or price.

    Args:
        name (str): Product name to search for.
        id (str): Product ID to search for.
        price (str): Product price to search for.

    Returns:
        List[Product]: List of products matching the search criteria.

    Raises:
        ProductNotFoundError: If no products match the search.
        HTTPException: For general server errors.
    """
    try:
        search_params = ProductSearch(name=name, id=id, price=price)
        products = product_db.get_product(**search_params.dict(exclude_none=True))
        if not products:
            raise ProductNotFoundError()
        for product in products:
            product["id"] = str(product.pop("_id", ""))
        return products
    except ProductNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Search failed")
        raise HTTPException(status_code=500, detail=str(e))
