from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from controllers.product_controller import ProductController
from schemas.product import RawProduct, CleanProduct, Review

# Create router
router = APIRouter(prefix="/products", tags=["products"])


@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_product(
    product: RawProduct,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Ingest a raw product and process it with AI in the background
    """
    try:
        product_controller = ProductController(db)
        result = product_controller.ingest_product(product)

        if "raw_id" in result:
            # Add AI processing as background task
            background_tasks.add_task(
                product_controller.process_product_with_ai, result["raw_id"])
            return result
        else:
            return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest product: {str(e)}"
        )


@router.get("/")
def get_products(
    status_filter: Optional[str] = None,
    processing_status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get products with optional filtering
    """
    try:
        product_controller = ProductController(db)
        return product_controller.get_products(
            status_filter=status_filter,
            processing_status=processing_status,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get products: {str(e)}"
        )


@router.post("/review/{clean_product_id}")
def review_product(
    clean_product_id: int,
    review: Review,
    db: Session = Depends(get_db)
):
    """
    Review a clean product (approve/reject)
    """
    try:
        product_controller = ProductController(db)
        return product_controller.review_product(clean_product_id, review)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review product: {str(e)}"
        )


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """
    Get processing statistics
    """
    try:
        product_controller = ProductController(db)
        return product_controller.get_stats()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )
