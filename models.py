# models.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class TaskCreate(BaseModel):
    url: str
    client: str

class TaskDb(TaskCreate):
    id: str
    product_name: Optional[str] = None
    status: str = "pending"  # pending, success, error
    created_at: datetime = Field(default_factory=datetime.astimezone  ) #utc time to time
    finished_at: Optional[datetime] = None

class Product(BaseModel):
    id: Optional[str]
    name: str
    price: Optional[str]
    images: List[str]
    # about_this_item: Optional[str]
    colors: List[str]
    sizes: List[str]
    url: str

class ProductSearch(BaseModel):
    name: Optional[str] = None
    id: Optional[str] = None
    price: Optional[str] = None
