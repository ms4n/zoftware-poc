from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from loguru import logger

from database import RawProduct, CleanProduct, Review as ReviewModel
from services.product_service import ProductService
from services.ai_service import AIService
from schemas.product import RawProduct as RawProductModel, CleanProduct as CleanProductModel, Review, ProductResponse, ReviewStatus


class ProductController:
    def __init__(self, db: Session):
        self.db = db
        self.product_service = ProductService(db)
        self.ai_service = AIService()

    def ingest_product(self, product: RawProductModel) -> Dict[str, Any]:
        """Ingest a raw product and return result"""
        try:
            result = self.product_service.create_raw_product(product)
            return result
        except Exception as e:
            raise Exception(f"Failed to ingest product: {str(e)}")

    def bulk_ingest_products(self, products: List[RawProductModel]) -> Dict[str, Any]:
        """Ingest multiple raw products in bulk and return result"""
        try:
            result = self.product_service.bulk_create_raw_products(products)
            return result
        except Exception as e:
            raise Exception(f"Failed to bulk ingest products: {str(e)}")

    def get_products(
        self,
        status_filter: Optional[str] = None,
        processing_status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ProductResponse]:
        """Get products with filtering and pagination"""
        try:
            return self.product_service.get_products(
                status_filter=status_filter,
                processing_status=processing_status,
                limit=limit,
                offset=offset
            )
        except Exception as e:
            raise Exception(f"Failed to get products: {str(e)}")

    def review_product(self, clean_product_id: int, review: Review) -> Dict[str, Any]:
        """Review a clean product (approve/reject)"""
        try:
            # Get clean product
            clean_product = self.db.query(CleanProduct).filter(
                CleanProduct.id == clean_product_id).first()
            if not clean_product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Clean product not found"
                )

            # Update status based on review action
            if review.action == "approve":
                clean_product.status = ReviewStatus.APPROVED
            elif review.action == "reject":
                clean_product.status = ReviewStatus.REJECTED
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid action. Must be 'approve' or 'reject'"
                )

            # Save review
            db_review = ReviewModel(
                clean_product_id=clean_product_id,
                action=review.action,
                reason=review.reason
            )

            self.db.add(db_review)
            self.db.commit()

            return {"message": f"Product {review.action}", "product_id": clean_product_id}

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to review product: {str(e)}")

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        try:
            return self.product_service.get_stats()
        except Exception as e:
            raise Exception(f"Failed to get stats: {str(e)}")

    def process_product_with_ai(self, raw_id: int):
        """Process raw product with AI"""
        try:
            # Get raw product
            raw_product = self.db.query(RawProduct).filter(
                RawProduct.id == raw_id).first()
            if not raw_product:
                return

            # Update status to processing
            self.product_service.update_processing_status(raw_id, "processing")

            # Prepare data for AI
            raw_data = {
                "name": raw_product.name,
                "website": raw_product.website,
                "category": raw_product.category,
                "description": raw_product.description
            }

            # Process with AI
            ai_result = self.ai_service.process_product(raw_data)

            # Save clean product
            if self.product_service.create_clean_product(raw_id, ai_result):
                # Update raw product status
                self.product_service.update_processing_status(
                    raw_id, "completed")

        except Exception as e:
            # Update status to failed
            self.product_service.update_processing_status(raw_id, "failed")
            raise e

    def bulk_process_products_with_ai(self, raw_ids: List[int]):
        """Process multiple raw products with AI in batches"""
        try:
            if not raw_ids:
                return

            # Prepare products for AI processing
            if not self.product_service.bulk_process_products_with_ai(raw_ids):
                return

            # Get raw products data for AI processing
            raw_products = self.db.query(RawProduct).filter(
                RawProduct.id.in_(raw_ids)
            ).all()

            # Prepare data for AI
            products_data = []
            for raw_product in raw_products:
                products_data.append({
                    "id": raw_product.id,
                    "name": raw_product.name,
                    "website": raw_product.website,
                    "category": raw_product.category,
                    "description": raw_product.description
                })

            # Process with AI in batch
            ai_results = self.ai_service.process_multiple_products(
                products_data)

            # Save clean products
            if self.product_service.bulk_create_clean_products(ai_results):
                # Update raw product statuses to completed
                for raw_id in raw_ids:
                    self.product_service.update_processing_status(
                        raw_id, "completed")
                logger.info(
                    f"Successfully processed {len(raw_ids)} products with AI")
            else:
                # Update statuses to failed
                for raw_id in raw_ids:
                    self.product_service.update_processing_status(
                        raw_id, "failed")

        except Exception as e:
            # Update statuses to failed
            for raw_id in raw_ids:
                self.product_service.update_processing_status(raw_id, "failed")
            logger.error(f"Bulk AI processing failed: {e}")
            raise e
