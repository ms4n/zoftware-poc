from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from loguru import logger

from database import RawProduct, CleanProduct, Review
from schemas.product import RawProduct as RawProductModel, CleanProduct as CleanProductModel, Review as ReviewModel, ProductResponse


class ProductService:
    def __init__(self, db: Session):
        self.db = db

    def create_raw_product(self, product: RawProductModel) -> Dict[str, Any]:
        """Create a new raw product"""
        try:
            # Check if product already exists
            existing = self.db.query(RawProduct).filter(
                RawProduct.name == product.name).first()
            if existing:
                return {"message": "Product already exists", "raw_id": existing.id}

            # Save raw product
            db_product = RawProduct(
                name=product.name,
                description=product.description,
                website=product.website,
                logo=product.logo,
                category=product.category,
                processing_status="pending"
            )

            self.db.add(db_product)
            self.db.commit()
            self.db.refresh(db_product)

            logger.info(
                f"Product created: {product.name} (ID: {db_product.id})")
            return {
                "message": "Product created successfully",
                "raw_id": db_product.id,
                "status": "pending"
            }

        except Exception as e:
            logger.error(f"Error creating raw product: {e}")
            self.db.rollback()
            raise Exception(f"Failed to create product: {str(e)}")

    def get_products(
        self,
        status_filter: Optional[str] = None,
        processing_status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ProductResponse]:
        """Get products with filtering and pagination"""
        try:
            query = self.db.query(RawProduct).outerjoin(CleanProduct)

            # Apply filters
            if status_filter:
                query = query.filter(CleanProduct.status == status_filter)

            if processing_status:
                query = query.filter(
                    RawProduct.processing_status == processing_status)

            # Apply pagination
            products = query.offset(offset).limit(limit).all()

            # Convert to response model
            result = []
            for raw_product in products:
                clean_product = self.db.query(CleanProduct).filter(
                    CleanProduct.raw_product_id == raw_product.id
                ).first()

                response = ProductResponse(
                    id=raw_product.id,
                    name=raw_product.name,
                    description=raw_product.description,
                    website=raw_product.website,
                    logo=raw_product.logo,
                    category=clean_product.category if clean_product else None,
                    status=clean_product.status if clean_product else "pending",
                    processing_status=raw_product.processing_status,
                    created_at=raw_product.created_at,
                    updated_at=raw_product.updated_at
                )
                result.append(response)

            return result

        except Exception as e:
            logger.error(f"Error getting products: {e}")
            raise Exception(f"Failed to get products: {str(e)}")

    def update_processing_status(self, raw_id: int, status: str) -> bool:
        """Update the processing status of a raw product"""
        try:
            raw_product = self.db.query(RawProduct).filter(
                RawProduct.id == raw_id).first()
            if not raw_product:
                return False

            raw_product.processing_status = status
            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Error updating processing status: {e}")
            self.db.rollback()
            return False

    def create_clean_product(self, raw_id: int, ai_result: Dict[str, str]) -> bool:
        """Create a clean product from AI processing result"""
        try:
            clean_product = CleanProduct(
                raw_product_id=raw_id,
                description=ai_result["description"],
                category=ai_result["category"],
                status="pending"
            )

            self.db.add(clean_product)
            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Error creating clean product: {e}")
            self.db.rollback()
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        try:
            # Raw products stats
            total_raw = self.db.query(RawProduct).count()
            pending_raw = self.db.query(RawProduct).filter(
                RawProduct.processing_status == "pending").count()
            processing_raw = self.db.query(RawProduct).filter(
                RawProduct.processing_status == "processing").count()
            completed_raw = self.db.query(RawProduct).filter(
                RawProduct.processing_status == "completed").count()
            failed_raw = self.db.query(RawProduct).filter(
                RawProduct.processing_status == "failed").count()

            # Clean products stats
            total_clean = self.db.query(CleanProduct).count()
            pending_review = self.db.query(CleanProduct).filter(
                CleanProduct.status == "pending").count()
            approved = self.db.query(CleanProduct).filter(
                CleanProduct.status == "approved").count()
            rejected = self.db.query(CleanProduct).filter(
                CleanProduct.status == "rejected").count()

            return {
                "raw_products": {
                    "total": total_raw,
                    "pending": pending_raw,
                    "processing": processing_raw,
                    "completed": completed_raw,
                    "failed": failed_raw
                },
                "clean_products": {
                    "total": total_clean,
                    "pending_review": pending_review,
                    "approved": approved,
                    "rejected": rejected
                }
            }

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            raise Exception(f"Failed to get stats: {str(e)}")
