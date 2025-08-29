from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ProductCategory(str, Enum):
    SALES_MARKETING = "sales_marketing"
    DEVTOOLS = "devtools"
    DATA_ANALYTICS = "data_analytics"
    PRODUCTIVITY = "productivity"
    FINANCE = "finance"
    OTHER = "other"


class RawProduct(BaseModel):
    name: str
    description: str
    website: str
    logo: Optional[str] = None
    category: Optional[str] = None


class CleanProduct(BaseModel):
    raw_product_id: int
    description: str
    category: ProductCategory
    status: ReviewStatus = ReviewStatus.PENDING


class Review(BaseModel):
    clean_product_id: int
    action: str  # "approve" or "reject"
    reason: Optional[str] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    website: str
    logo: Optional[str]
    category: Optional[ProductCategory]
    status: ReviewStatus
    processing_status: ProcessingStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
