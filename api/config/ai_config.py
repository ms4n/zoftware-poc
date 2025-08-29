"""
AI Processing Configuration
"""
from typing import Dict, Any

# OpenAI API Configuration
OPENAI_CONFIG = {
    "model": "gpt-4o-mini",
    "max_tokens": 10000,
    "temperature": 0.3,
    "response_format": {"type": "json_object"}
}

# Batch Processing Configuration
BATCH_CONFIG = {
    "max_products_per_request": 10,  # Maximum products per AI request
    "max_requests_per_minute": 3,    # OpenAI rate limit
    "batch_delay_seconds": 20,       # Delay between batches to respect rate limit
    "max_background_tasks": 20        # Maximum concurrent background tasks
}

# Product Processing Configuration
PROCESSING_CONFIG = {
    "default_category": "other",
    "description_sentences": 2,
    "valid_categories": [
        "sales_marketing",
        "devtools",
        "data_analytics",
        "productivity",
        "finance",
        "other"
    ]
}


def get_ai_config() -> Dict[str, Any]:
    """Get AI configuration"""
    return OPENAI_CONFIG.copy()


def get_batch_config() -> Dict[str, Any]:
    """Get batch processing configuration"""
    return BATCH_CONFIG.copy()


def get_processing_config() -> Dict[str, Any]:
    """Get product processing configuration"""
    return PROCESSING_CONFIG.copy()
