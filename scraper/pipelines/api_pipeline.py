import scrapy
import requests
import json
from loguru import logger
from typing import Dict, Any


class APIPipeline:
    """
    Pipeline to post scraped data directly to FastAPI endpoint
    """

    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.ingest_endpoint = f"{api_url}/ingest"

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """
        Process scraped item by posting to API
        """
        try:
            # Prepare data for API using new simplified schema
            api_data = {
                "name": item.get("product_name", ""),
                "description": item.get("description", ""),
                "website": item.get("website_link", ""),
                "logo": item.get("logo_src", ""),
                "category": item.get("category", {}).get("name", "")
            }

            # Post to API
            response = requests.post(
                self.ingest_endpoint,
                json=api_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            if response.status_code == 202:
                logger.success(
                    f"Product posted to API: {item.get('product_name', 'Unknown')}")
                item['api_status'] = 'accepted'
            else:
                logger.error(
                    f"API request failed: {response.status_code} - {response.text}")
                item['api_status'] = 'failed'

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error posting to API: {e}")
            item['api_status'] = 'network_error'
        except Exception as e:
            logger.error(f"Unexpected error in API pipeline: {e}")
            item['api_status'] = 'error'

        return item


class APIPipelineMiddleware:
    """
    Scrapy middleware to automatically post items to API
    """

    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url

    @classmethod
    def from_crawler(cls, crawler):
        api_url = crawler.settings.get('API_URL', 'http://localhost:8000')
        return cls(api_url)

    def process_item(self, item, spider):
        pipeline = APIPipeline(self.api_url)
        return pipeline.process_item(item, spider)
