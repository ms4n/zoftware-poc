from scraper.sites.g2 import G2Spider
from scraper.sites.capterra import CapterraSpider
from loguru import logger
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
import argparse
import os
import sys
import logging

# Add the scraper directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import other spiders here as they are created

# Spider registry
SPIDERS = {
    "capterra": CapterraSpider,
    "g2": G2Spider,
}


def run_spider(site_name: str):
    """
    Runs a spider from the registry based on the site name.
    """
    spider_class = SPIDERS.get(site_name)
    if not spider_class:
        logger.error(
            f"Spider for site '{site_name}' not found in the registry.")
        return

    try:
        # Set up Scrapy settings
        settings = get_project_settings()

        # Set the settings file path
        settings.set('SETTINGS_MODULE', 'scraper.settings')

        # Enable API pipeline
        settings.set('ITEM_PIPELINES', {
            'scraper.pipelines.api_pipeline.APIPipeline': 300,
        })

        # Set API URL
        settings.set('API_URL', 'http://127.0.0.1:8000')

        # Suppress Scrapy's verbose logging - only show errors
        settings.set("LOG_LEVEL", "ERROR")

        # Disable Scrapy's built-in logging
        settings.set("LOG_ENABLED", False)

        # Disable specific Scrapy extensions that generate noise
        settings.set("TELNETCONSOLE_ENABLED", False)
        settings.set("LOGSTATS_INTERVAL", 0)
        settings.set("MEMUSAGE_ENABLED", False)
        settings.set("MEMUSAGE_LIMIT_MB", 0)

        process = CrawlerProcess(settings)
        process.crawl(spider_class)
        process.start()
        logger.success(f"Successfully finished scraping {site_name}.")

    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run a web scraper for a specific site.")
    parser.add_argument(
        "site", help="The name of the site to scrape (e.g., 'capterra').")
    args = parser.parse_args()

    logger.info(f"Starting to scrape {args.site}...")
    run_spider(args.site)
