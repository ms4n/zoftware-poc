from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from datetime import datetime
import os

# Database URL
DATABASE_URL = "sqlite:///./zoftware.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite specific
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


class RawProduct(Base):
    __tablename__ = "raw_products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    website = Column(String, nullable=False)
    logo = Column(String)
    category = Column(String)
    processing_status = Column(
        SQLEnum("pending", "processing", "completed", "failed"), default="pending")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class CleanProduct(Base):
    __tablename__ = "clean_products"

    id = Column(Integer, primary_key=True, index=True)
    raw_product_id = Column(Integer, ForeignKey(
        "raw_products.id"), unique=True)
    description = Column(Text, nullable=False)
    category = Column(SQLEnum("sales_marketing", "devtools", "data_analytics",
                      "productivity", "finance", "other"), nullable=False)
    status = Column(SQLEnum("pending", "approved",
                    "rejected"), default="pending")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    clean_product_id = Column(Integer, ForeignKey("clean_products.id"))
    action = Column(String, nullable=False)  # "approve" or "reject"
    reason = Column(Text)
    created_at = Column(DateTime, default=func.now())


# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
