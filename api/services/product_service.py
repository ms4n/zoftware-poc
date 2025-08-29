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

    def bulk_create_raw_products(self, products: List[RawProductModel]) -> Dict[str, Any]:
        """Create multiple raw products in bulk"""
        try:
            results = []
            created_count = 0
            skipped_count = 0

            for product in products:
                # Check if product already exists
                existing = self.db.query(RawProduct).filter(
                    RawProduct.name == product.name).first()
                if existing:
                    results.append({
                        "name": product.name,
                        "status": "skipped",
                        "message": "Product already exists",
                        "raw_id": existing.id
                    })
                    skipped_count += 1
                    continue

                # Create raw product
                db_product = RawProduct(
                    name=product.name,
                    description=product.description,
                    website=product.website,
                    logo=product.logo,
                    category=product.category,
                    processing_status="pending"
                )
                self.db.add(db_product)
                results.append({
                    "name": product.name,
                    "status": "created",
                    "message": "Product created successfully",
                    "raw_id": None  # Will be set after commit
                })
                created_count += 1

            # Commit all changes
            self.db.commit()

            # Update raw_id for created products
            for i, result in enumerate(results):
                if result["status"] == "created":
                    # Get the product we just created to get its ID
                    created_product = self.db.query(RawProduct).filter(
                        RawProduct.name == result["name"]
                    ).first()
                    if created_product:
                        result["raw_id"] = created_product.id

            logger.info(
                f"Bulk insert completed: {created_count} created, {skipped_count} skipped")
            return {
                "total_processed": len(products),
                "created": created_count,
                "skipped": skipped_count,
                "results": results
            }

        except Exception as e:
            logger.error(f"Error in bulk create: {e}")
            self.db.rollback()
            raise Exception(f"Failed to bulk create products: {str(e)}")

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

    def bulk_create_clean_products(self, ai_results: List[Dict[str, Any]]) -> bool:
        """Create multiple clean products from AI processing results"""
        try:
            for result in ai_results:
                raw_id = result.get("product_id")
                if raw_id:
                    clean_product = CleanProduct(
                        raw_product_id=raw_id,
                        description=result["description"],
                        category=result["category"],
                        status="pending"
                    )
                    self.db.add(clean_product)

            self.db.commit()
            logger.info(
                f"Successfully created {len(ai_results)} clean products")
            return True

        except Exception as e:
            logger.error(f"Error creating clean products: {e}")
            self.db.rollback()
            return False

    def bulk_process_products_with_ai(self, raw_ids: List[int]) -> bool:
        """Process multiple raw products with AI in batches"""
        try:
            # Get raw products data
            raw_products = self.db.query(RawProduct).filter(
                RawProduct.id.in_(raw_ids)
            ).all()

            if not raw_products:
                logger.warning("No raw products found for AI processing")
                return False

            # Update status to processing
            for raw_product in raw_products:
                raw_product.processing_status = "processing"

            self.db.commit()

            # Prepare data for AI processing
            products_data = []
            for raw_product in raw_products:
                products_data.append({
                    "id": raw_product.id,
                    "name": raw_product.name,
                    "website": raw_product.website,
                    "category": raw_product.category,
                    "description": raw_product.description
                })

            # Process with AI (this will be called from the controller)
            logger.info(
                f"Prepared {len(products_data)} products for AI processing")
            return True

        except Exception as e:
            logger.error(f"Error preparing products for AI processing: {e}")
            # Reset status to pending on error
            for raw_product in raw_products:
                raw_product.processing_status = "pending"
            self.db.commit()
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
