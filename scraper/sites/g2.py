from urllib.parse import urljoin, urlparse
from scrapy import Request
from scraper.engine.base_spider import BaseSpider
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import random
import time
import json


class G2Spider(BaseSpider):
    name = "g2"
    start_urls = [
        "https://www.g2.com/categories/video-conferencing"
        # "https://www.g2.com/categories/development-services",  # subcategories - test later
    ]
    handle_httpstatus_list = [403, 404]

    # Number of random categories to sample (0 = all categories)
    SAMPLE_CATEGORY_COUNT = 2
    # Examples: 1 (POC), 5 (testing), 0 (production - all categories)

    SCRAPE_ALL_PAGES = False   # If True, scrape all pages; if False, use MAX_PAGES

    # Maximum number of pages to scrape per category (when SCRAPE_ALL_PAGES=False)
    MAX_PAGES = 1

    USE_ROTATING_PROXIES = False  # Enable/disable rotating proxies

    # G2-specific selectors for JS-rendered content
    CATEGORIES_TABLE_SELECTOR = "//table[@class='categories__table']"
    CATEGORY_ROW_SELECTOR = "//div[@class='categories__row']"
    CATEGORY_LINK_SELECTOR = ".//div[@class='categories__name']//a[@class='link js-log-click']"
    PAGE_NOT_FOUND_XPATH = "//h1[contains(text(),'404')]"

    # Selectors for subcategory detection and extraction
    SUBCATEGORY_SECTION_SELECTOR = "//h2[contains(text(), 'Categories')] | //h1[contains(text(), 'Categories')] | //div[contains(@class, 'categories')]"
    SUBCATEGORY_LINK_SELECTOR = "//a[contains(@href, '/categories/') and not(contains(@href, '?'))]"

    # Selectors for direct product listings (updated to match actual G2 structure)
    PRODUCT_LISTING_SECTION_SELECTOR = "//div[contains(text(), 'Listings in')] | //div[contains(text(), 'listings')]"
    PRODUCT_CARD_SELECTOR = "//div[@class='segmented-shadow-card__segment segmented-shadow-card__segment--multi-part'] | //div[@class='product-card']"

    async def start(self):
        """
        Starts the requests to the hardcoded category pages.
        """
        for url in self.start_urls:
            yield Request(url, callback=self.parse)

    def parse(self, response):
        """
        Parses a category page and determines if it has subcategories or direct products.
        """
        self.log.info(f"Parsing G2 category page: {response.url}")

        # Initialize browser driver for JS rendering
        self.init_driver(headless=False)

        try:
            # Navigate to the page and wait for JS to render
            title = self.navigate_to_page(response.url, wait_time=5)
            self.log.info(f"Page title: {title}")

            page_type = "direct_products"
            self.log.info(
                f"Forcing page type to: {page_type} (for testing direct products)")

            if page_type == "subcategories":
                yield from self.handle_subcategories_page(response)
            elif page_type == "direct_products":
                yield from self.handle_direct_products_page(response)
            else:
                self.log.warning(f"Unknown page type for {response.url}")

        except Exception as e:
            self.log.error(f"Error in parse method: {str(e)}")

    def detect_page_type(self):
        """
        Detect if the current page has subcategories or direct product listings.
        """
        # Wait for page content to load
        time.sleep(2)

        subcategory_elements = self.find_elements_safe(
            "xpath", self.SUBCATEGORY_SECTION_SELECTOR, timeout=8)

        # Check for subcategory links to confirm
        subcategory_links = self.find_elements_safe(
            "xpath", self.SUBCATEGORY_LINK_SELECTOR, timeout=5)

        if subcategory_elements and subcategory_links:
            self.log.info(
                f"Found subcategories section with {len(subcategory_links)} subcategory links")
            return "subcategories"

        # Check for direct product listings
        product_listing_elements = self.find_elements_safe(
            "xpath", self.PRODUCT_LISTING_SECTION_SELECTOR, timeout=5)

        # Check for product cards to confirm
        product_cards = self.find_elements_safe(
            "xpath", self.PRODUCT_CARD_SELECTOR, timeout=5)

        if product_listing_elements or product_cards:
            self.log.info(
                f"Found direct product listings with {len(product_cards)} product cards")
            return "direct_products"

        # Log page content for debugging if nothing found
        self.log.warning(
            "Could not determine page type. Logging page content...")
        page_text = self.driver.find_element(By.TAG_NAME, "body").text[:500]
        self.log.warning(f"Page content preview: {page_text}")

        return "unknown"

    def handle_subcategories_page(self, response):
        """
        Handle a page that contains subcategories.
        """
        self.log.info("Handling subcategories page")

        subcategory_links = self.find_elements_safe(
            "xpath", self.SUBCATEGORY_LINK_SELECTOR)

        if not subcategory_links:
            self.log.warning("No subcategory links found")
            return

        self.log.success(f"Found {len(subcategory_links)} subcategory links")

        # Extract and follow subcategory links
        for link in subcategory_links:
            try:
                href = link.get_attribute("href")
                name = link.text.strip()

                if href and name:
                    full_url = urljoin(response.url, href)
                    self.log.info(
                        f"Following subcategory: {name} -> {full_url}")
                    yield Request(
                        full_url,
                        callback=self.parse_category,
                        meta={'page_num': 1, 'category_name': name}
                    )
            except Exception as e:
                self.log.warning(
                    f"Error processing subcategory link: {str(e)}")

    def handle_direct_products_page(self, response):
        """
        Handle a page that contains direct product listings.
        """
        self.log.info("Handling direct products page")

        # Extract category info from URL
        category_slug, category_name = self.extract_category_info(response.url)

        yield Request(
            response.url,
            callback=self.parse_category,
            meta={'page_num': 1, 'category_name': category_name},
            dont_filter=True  # Allow re-processing of the same URL
        )

    def parse_category(self, response):
        """
        Parses a category page to extract software listings.
        """
        # selectors based on consistent G2 class patterns
        PRODUCT_CARD_SELECTOR = "//div[contains(@class, 'segmented-shadow-card__segment')]"

        PRODUCT_NAME_SELECTOR = ".//div[@itemprop='name']"
        PRODUCT_LINK_SELECTOR = ".//a[.//div[@itemprop='name']]"
        LOGO_SELECTOR = ".//img[@itemprop='image']"
        DESCRIPTION_SELECTOR = ".//span[contains(@class, 'product-listing__paragraph') and contains(@class, 'x-truncate-revealer-initialized')]"
        PAGINATION_NEXT_SELECTOR = "//a[@rel='next'] | //a[contains(@class, 'pagination__item') and contains(text(), 'Next')]"

        self.init_driver(headless=False)
        try:
            title = self.navigate_to_page(response.url, wait_time=5)
            self.log.info(f"Parsing category page: {title}")

            if self.find_elements_safe("xpath", self.PAGE_NOT_FOUND_XPATH):
                self.log.warning(
                    f"Page not found at {response.url}, stopping pagination for this category."
                )
                return

            category_slug, category_name = self.extract_category_info(
                response.url)

            # Wait a bit more for dynamic content
            time.sleep(3)

            product_cards = self.find_elements_safe(
                "xpath", PRODUCT_CARD_SELECTOR, timeout=10)

            if not product_cards:
                self.log.warning(
                    f"No product listings found on {response.url}")
                self.log.info("Trying alternative selectors for debugging...")
                alt_cards1 = self.find_elements_safe(
                    "xpath", "//div[contains(@class, 'product-card')]")
                alt_cards2 = self.find_elements_safe(
                    "xpath", "//div[contains(@class, 'segmented-shadow-card')]")
                alt_cards3 = self.find_elements_safe(
                    "xpath", "//div[@itemprop='name']")
                self.log.info(
                    f"Alt selector 1 (product-card): {len(alt_cards1)} elements")
                self.log.info(
                    f"Alt selector 2 (segmented-shadow-card): {len(alt_cards2)} elements")
                self.log.info(
                    f"Alt selector 3 (itemprop=name): {len(alt_cards3)} elements")
                return

            self.log.success(
                f"Found {len(product_cards)} product listings on page.")

            for card in product_cards:
                listing_data = self.extract_product_data(
                    card, category_slug, category_name, response.url,
                    PRODUCT_NAME_SELECTOR, PRODUCT_LINK_SELECTOR, LOGO_SELECTOR, DESCRIPTION_SELECTOR)
                if listing_data:
                    self.log.info(
                        f"Scraped product data:\n{json.dumps(listing_data, indent=2)}")

            # Handle pagination
            next_request = self.handle_pagination(
                response, category_name, PAGINATION_NEXT_SELECTOR)
            if next_request:
                yield next_request

        except Exception as e:
            self.log.error(f"Error in parse_category method: {str(e)}")

    def extract_category_info(self, url):
        """Extract category slug and name from URL"""
        path = urlparse(url).path
        # Assuming URL structure like /categories/crm
        category_slug = path.strip("/").split("/")[-1]
        category_name = category_slug.replace("-", " ").title()
        return category_slug, category_name

    def extract_product_data(self, card, category_slug, category_name, base_url,
                             name_selector, link_selector, logo_selector, description_selector):
        """Extract core product data from a single product card"""

        try:
            # Extract product name
            product_name = self.extract_text_safe(card, name_selector)
            if not product_name:
                self.log.warning("Product name not found, skipping card")
                return None

            # Extract product link
            product_link_relative = self.extract_attribute_safe(
                card, link_selector, "href")
            product_link = urljoin(
                base_url, product_link_relative) if product_link_relative else ""

            # Extract logo (prefer data-deferred-image-src over src to get actual URL)
            logo_src = self.extract_attribute_safe(
                card, logo_selector, "data-deferred-image-src")
            if not logo_src or logo_src.startswith("data:image"):
                logo_src = self.extract_attribute_safe(
                    card, logo_selector, "src")
            # Filter out data: URLs completely
            if logo_src and logo_src.startswith("data:image"):
                logo_src = ""

            # Extract description with robust approach
            description = self.extract_full_description(
                card, description_selector)

            return {
                "product_name": product_name,
                "description": description,
                "website_link": product_link,
                "logo_src": logo_src,
                "category": {"slug": category_slug, "name": category_name},
            }

        except Exception as e:
            self.log.warning(f"Error extracting product data: {str(e)}")
            return None

    def extract_full_description(self, card, description_selector):
        """Extract complete product description using two-part structure"""
        try:
            # Find description specifically within this card's scope
            desc_element = None

            # First try: look for description within the current card
            try:
                desc_element = card.find_element(
                    By.XPATH, description_selector)
            except:
                # Second try: look for description in the immediate parent product-card
                try:
                    product_card = card.find_element(
                        By.XPATH, ".//div[contains(@class, 'product-card')]")
                    desc_element = product_card.find_element(
                        By.XPATH, description_selector)
                except:
                    # Third try: look for any description span within this specific card's DOM tree
                    try:
                        desc_element = card.find_element(
                            By.XPATH, ".//span[contains(@class, 'product-listing__paragraph')]")
                    except:
                        pass

            if desc_element:
                # Get the visible text (first part) - this is ALWAYS available
                visible_text = desc_element.text.strip()

                # Clean visible text by removing "Show More" and trailing dots
                if "Show More" in visible_text:
                    visible_text = visible_text.split("Show More")[0].strip()
                visible_text = visible_text.replace("...", "").strip()

                # Try to get overflow text (second part) from attribute
                overflow_text = ""
                try:
                    overflow_text = desc_element.get_attribute(
                        "data-truncate-revealer-overflow-text")
                    if overflow_text:
                        overflow_text = overflow_text.strip()
                except:
                    pass

                # If we have both parts, combine them
                if visible_text and overflow_text:
                    complete_description = visible_text + " " + overflow_text
                    return " ".join(complete_description.split())

                # If we only have visible text (short descriptions), return it
                elif visible_text:
                    return " ".join(visible_text.split())

                # Fallback: try to get hidden text from span (legacy method)
                else:
                    try:
                        hidden_span = desc_element.find_element(
                            By.XPATH, ".//span[@class='hide-if-js']")
                        hidden_text = hidden_span.text.strip()
                        if hidden_text:
                            # Combine visible + hidden span text
                            full_description = visible_text + " " + hidden_text
                            return " ".join(full_description.split())
                    except:
                        pass

                # Final fallback: return visible text if nothing else works
                return " ".join(visible_text.split()) if visible_text else ""

            return ""

        except Exception as e:
            self.log.warning(f"Error extracting description: {str(e)}")
            return ""

    def handle_pagination(self, response, category_name, pagination_selector):
        """Handle pagination logic for G2 based on configuration"""
        current_page = response.meta.get('page_num', 1)

        should_continue = False
        if self.SCRAPE_ALL_PAGES:
            should_continue = True
            limit_info = "all pages"
        else:
            should_continue = current_page < self.MAX_PAGES
            limit_info = f"max {self.MAX_PAGES} pages"

        if should_continue:
            next_page_elements = self.find_elements_safe(
                "xpath", pagination_selector)
            if next_page_elements:
                next_page_element = next_page_elements[0]
                next_page_url = next_page_element.get_attribute("href")
                next_page_url = urljoin(response.url, next_page_url)
                next_page_num = current_page + 1

                self.log.info(
                    f"Scraping next page ({next_page_num}) for category '{category_name}': {next_page_url}"
                )
                return Request(next_page_url, callback=self.parse_category, meta={'page_num': next_page_num})

        self.log.success(
            f"Finished scraping category '{category_name}'. Reached limit ({limit_info})."
        )
        return None
