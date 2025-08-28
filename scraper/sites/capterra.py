from urllib.parse import urljoin, urlparse, urlencode, parse_qs, urlunparse
from scrapy import Request
from scraper.engine.base_spider import BaseSpider
import random


class CapterraSpider(BaseSpider):
    name = "capterra"
    start_urls = ["https://www.capterra.in/directory"]
    handle_httpstatus_list = [403, 404]

    # Number of random categories to sample (0 = all categories)
    SAMPLE_CATEGORY_COUNT = 2
    # Examples: 1 (POC), 5 (testing), 0 (production - all categories)

    SCRAPE_ALL_PAGES = False   # If True, scrape all pages; if False, use MAX_PAGES
    # WARNING: Setting to True may scrape thousands of products

    # Maximum number of pages to scrape per category (when SCRAPE_ALL_PAGES=False)
    MAX_PAGES = 1
    # Examples: 1 (quick test), 5 (moderate), 10+ (production)

    USE_ROTATING_PROXIES = False  # Enable/disable rotating proxies

    # Capterra-specific selectors
    CATEGORY_LINKS_SELECTOR = "//div[@id='categories_list']/a"
    PRODUCT_CARD_CLASS = "product-card"
    PRODUCT_NAME_XPATH = './/a[@data-evcmp="product-card" and @data-evdtl="text-link_product-name"]'
    MOBILE_DESC_XPATH = './/div[contains(@class, "d-lg-none")]'
    HIDDEN_DESC_XPATH = './/span[contains(@class, "read-more__hidden")]'
    VISIBLE_DESC_XPATH = './/span[contains(@class, "read-more__visible")]'
    LOGO_XPATH = './/a[contains(@class, "logo-container")]//img'
    PAGE_NOT_FOUND_XPATH = "//h1[text()='Page not found']"

    async def start(self):
        """
        Starts the requests to the Capterra directory page.
        """
        for url in self.start_urls:
            yield Request(url, callback=self.parse)

    def parse(self, response):
        """
        Parses the main directory page, extracts product links, and follows them.
        """
        # Initialize Chrome driver (headless=False for Cloudflare bypass)
        self.init_driver(headless=False)

        try:
            # Navigate to the page using base spider method
            title = self.navigate_to_page(response.url)
            self.log.info(f"Page title: {title}")

            # Extract category links using base spider method
            category_links = self.find_elements_safe(
                "xpath", self.CATEGORY_LINKS_SELECTOR)

            if not category_links:
                self.log.warning("No category links found on the page.")
                return

            self.log.success(f"Found {len(category_links)} category links.")

            # Apply category sampling based on configuration
            if self.SAMPLE_CATEGORY_COUNT == 0:
                # Scrape all categories
                sample_links = category_links
            else:
                # Sample specified number of categories
                sample_count = min(
                    self.SAMPLE_CATEGORY_COUNT, len(category_links))
                sample_links = random.sample(category_links, sample_count)

            self.log.info(
                f"Processing {len(sample_links)} category links (configured: {self.SAMPLE_CATEGORY_COUNT}).")

            for link_element in sample_links:
                href = link_element.get_attribute("href")
                if href:
                    # Append sort=popularity to get listings sorted by popularity
                    full_url = urljoin(response.url, href) + "?sort=popularity"
                    self.log.info(
                        f"Following random category link: {full_url}")
                    yield Request(full_url, callback=self.parse_category)

        except Exception as e:
            self.log.error(f"Error in parse method: {str(e)}")

    def parse_category(self, response):
        """
        Parses a category page to extract software listings.
        """
        try:
            # Navigate to the page using base spider method
            title = self.navigate_to_page(response.url)
            self.log.info(f"Parsing category page: {title}")

            # Check for "Page not found" to stop pagination
            if self.find_elements_safe("xpath", self.PAGE_NOT_FOUND_XPATH):
                self.log.warning(
                    f"Page not found at {response.url}, stopping pagination for this category."
                )
                return

            # Extract category information from URL
            category_slug, category_name = self.extract_category_info(
                response.url)

            # Find product cards using base spider method
            product_cards = self.find_elements_safe(
                "class", self.PRODUCT_CARD_CLASS)

            if not product_cards:
                self.log.warning(
                    f"No product listings found on {response.url}")
                return

            self.log.success(
                f"Found {len(product_cards)} product listings on page.")

            # Extract data from each product card
            for card in product_cards:
                listing_data = self.extract_product_data(
                    card, category_slug, category_name, response.url)
                self.log.info(f"Scraped data: {listing_data}")

            # Handle pagination
            next_request = self.handle_pagination(response, category_name)
            if next_request:
                yield next_request

        except Exception as e:
            self.log.error(f"Error in parse_category method: {str(e)}")

    def extract_category_info(self, url):
        """Extract category slug and name from URL"""
        path = urlparse(url).path
        category_slug = path.strip("/").split("/")[-2]
        category_name = category_slug.replace("-", " ").title()
        return category_slug, category_name

    def extract_product_data(self, card, category_slug, category_name, base_url):
        """Extract all product data from a single product card"""
        # Extract product name and link
        product_name = self.extract_text_safe(card, self.PRODUCT_NAME_XPATH)
        product_link_relative = self.extract_attribute_safe(
            card, self.PRODUCT_NAME_XPATH, "href")
        product_link = urljoin(
            base_url, product_link_relative) if product_link_relative else ""

        # Extract description using multiple strategies
        description = self.extract_description(card)

        # Extract logo
        logo_src = self.extract_attribute_safe(card, self.LOGO_XPATH, "src")

        return {
            "product_name": product_name,
            "description": description,
            "website_link": product_link,
            "logo_src": logo_src,
            "category": {"slug": category_slug, "name": category_name},
        }

    def extract_description(self, card):
        """Extract description using multiple fallback strategies"""
        # Strategy 1: Mobile description (always visible)
        description = self.extract_text_safe(card, self.MOBILE_DESC_XPATH)

        # Strategy 2: Hidden description (full text)
        if not description:
            description = self.extract_text_safe(card, self.HIDDEN_DESC_XPATH)

        # Strategy 3: Visible description (partial text)
        if not description:
            description = self.extract_text_safe(card, self.VISIBLE_DESC_XPATH)

        return description

    def handle_pagination(self, response, category_name):
        """Handle pagination logic for Capterra based on configuration"""
        parsed_url = urlparse(response.url)
        query_params = parse_qs(parsed_url.query)
        current_page = int(query_params.get("page", [1])[0])

        # Determine if we should continue to next page based on configuration
        should_continue = False
        if self.SCRAPE_ALL_PAGES:
            should_continue = True
            limit_info = "all pages"
        else:
            should_continue = current_page < self.MAX_PAGES
            limit_info = f"max {self.MAX_PAGES} pages"

        if should_continue:
            next_page_num = current_page + 1
            query_params["page"] = [str(next_page_num)]
            new_query_string = urlencode(query_params, doseq=True)
            next_page_url = urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                new_query_string,
                parsed_url.fragment,
            ))

            self.log.info(
                f"Scraping next page ({next_page_num}) for category '{category_name}': {next_page_url}"
            )
            return Request(next_page_url, callback=self.parse_category)
        else:
            self.log.success(
                f"Finished scraping category '{category_name}'. Reached limit ({limit_info})."
            )
