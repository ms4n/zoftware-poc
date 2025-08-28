import argparse
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from loguru import logger

from scraper.sites.capterra import CapterraSpider
# Import other spiders here as they are created
# from scraper.sites.g2 import G2Spider

# Spider registry
SPIDERS = {
    "capterra": CapterraSpider,
    # "g2": G2Spider,
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
        settings.set("LOG_LEVEL", "WARNING")

        # Add required settings for scrapy-playwright
        settings.set("DOWNLOAD_HANDLERS", {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        })
        settings.set("TWISTED_REACTOR",
                     "twisted.internet.asyncioreactor.AsyncioSelectorReactor")

        process = CrawlerProcess(settings)
        process.crawl(spider_class)
        process.start()
        logger.info(f"Finished scraping {site_name}.")

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
