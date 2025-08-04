from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class TaskCreate(BaseModel):
    url: str
    client: str

class Product(BaseModel):
    id: Optional[str]
    name: str
    price: Optional[str]
    images: Optional[List[Optional[str]]] = None
    colors: Optional[List[Optional[str]]] = None
    sizes: Optional[List[Optional[str]]] = None
    url: str


class ProductSearch(BaseModel):
    name: Optional[str] = None
    id: Optional[str] = None
    price: Optional[str] = None
