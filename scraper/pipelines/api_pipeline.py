import scrapy
import requests
import json
from loguru import logger
from typing import Dict, Any, List


class APIPipeline:
    """
    Pipeline to collect scraped data and post to FastAPI endpoint in bulk
    """

    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.ingest_endpoint = f"{api_url}/products/ingest/bulk"
        self.collected_items = []

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """
        Collect scraped item instead of posting immediately
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

            # Add to collection instead of posting immediately
            self.collected_items.append(api_data)

            # Mark item as collected
            item['api_status'] = 'collected'
            logger.info(
                f"Item collected: {item.get('product_name', 'Unknown')}")

        except Exception as e:
            logger.error(f"Error collecting item: {e}")
            item['api_status'] = 'error'

        return item

    def close_spider(self, spider):
        """
        Post all collected items to API when spider closes
        """
        if not self.collected_items:
            logger.info("No items to post to API")
            return

        try:
            logger.info(
                f"Posting {len(self.collected_items)} items to API in bulk")

            # Post all items in bulk
            response = requests.post(
                self.ingest_endpoint,
                json=self.collected_items,
                headers={"Content-Type": "application/json"},
                timeout=60  # Increased timeout for bulk operations
            )

            if response.status_code == 202:
                logger.success(
                    f"Successfully posted {len(self.collected_items)} items to API")

                # Log the response details
                try:
                    response_data = response.json()
                    logger.info(
                        f"API Response: {response_data.get('created', 0)} created, {response_data.get('skipped', 0)} skipped")
                except:
                    logger.info("API response received successfully")

            else:
                logger.error(
                    f"Bulk API request failed: {response.status_code} - {response.text}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error posting to API: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in bulk API pipeline: {e}")


class APIPipelineMiddleware:
    """
    Scrapy middleware to automatically collect items for bulk API posting
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
