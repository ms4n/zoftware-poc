from urllib.parse import urljoin
from scrapy import Request
from scraper.engine.base_spider import BaseSpider
from scrapy_playwright.page import PageMethod
import time
import random


class CapterraSpider(BaseSpider):
    name = "capterra"
    start_urls = ["https://www.capterra.in/directory"]

    async def start(self):
        """
        Starts the requests to the Capterra directory page.
        """
        for url in self.start_urls:
            yield Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
                },
                meta=dict(
                    playwright=True,
                    playwright_include_page=True,
                    playwright_page_methods=self.get_page_methods(),
                ),
                callback=self.parse,
            )

    async def parse(self, response):
        """
        Parses the main directory page, extracts product links, and follows them.
        """
        page = response.meta["playwright_page"]

        # Log the title to confirm the page was loaded
        title = await page.title()
        self.log.info(f"Page title: {title}")

        # Extract category links from the directory page
        category_links_locator = page.locator("//div[@id='categories_list']/a")
        category_links = await category_links_locator.all()

        if not category_links:
            self.log.warning("No category links found on the page.")
            await page.close()
            return

        self.log.info(f"Found {len(category_links)} category links.")

        # For this POC, we'll process a random sample of 3 categories to avoid excessive data.
        # To scrape all categories, iterate over `category_links` directly.
        sample_links = (
            random.sample(category_links, 3)
            if len(category_links) > 3
            else category_links
        )

        self.log.info(f"Processing {len(sample_links)} random category links.")

        for link_element in sample_links:
            href = await link_element.get_attribute("href")
            if href:
                full_url = urljoin(response.url, href)
                self.log.info(f"Following random category link: {full_url}")
                yield Request(
                    full_url,
                    callback=self.parse_category,
                    meta=dict(
                        playwright=True,
                        playwright_include_page=True,
                        playwright_page_methods=self.get_page_methods(),
                    ),
                )

        await page.close()

    async def parse_category(self, response):
        """
        Parses a category page to extract software listings.
        """
        page = response.meta["playwright_page"]
        title = await page.title()
        self.log.info(f"Parsing category page: {title}")

        # TODO: Extract software listings from this page.

        await page.close()
