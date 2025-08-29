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


@router.post("/ingest/bulk", status_code=status.HTTP_202_ACCEPTED)
async def bulk_ingest_products(
    products: List[RawProduct],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Ingest multiple raw products in bulk and process them with AI in the background
    """
    try:
        product_controller = ProductController(db)
        result = product_controller.bulk_ingest_products(products)

        # Add bulk AI processing as background task for all created products
        if "results" in result:
            created_product_ids = [
                product_result["raw_id"]
                for product_result in result["results"]
                if product_result["status"] == "created" and product_result["raw_id"]
            ]

            if created_product_ids:
                # Process products in batches of 10 to respect rate limits
                batch_size = 10
                for i in range(0, len(created_product_ids), batch_size):
                    batch_ids = created_product_ids[i:i + batch_size]
                    background_tasks.add_task(
                        product_controller.bulk_process_products_with_ai, batch_ids)

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk ingest products: {str(e)}"
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
