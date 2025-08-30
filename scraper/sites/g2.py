from urllib.parse import urljoin, urlparse
from scrapy import Request
from scraper.engine.base_spider import BaseSpider
from selenium.webdriver.common.by import By
import random
import time
import json


class G2Spider(BaseSpider):
    name = "g2"
    start_urls = [
        "https://www.g2.com/categories/influencer-marketing-platforms"  # Main categories page
    ]
    handle_httpstatus_list = [403, 404]

    # Number of random categories to sample (0 = all categories)
    SAMPLE_CATEGORY_COUNT = 1

    SCRAPE_ALL_PAGES = False   # If True, scrape all pages; if False, use MAX_PAGES

    # Maximum number of pages to scrape per category (when SCRAPE_ALL_PAGES=False)
    MAX_PAGES = 1

    USE_ROTATING_PROXIES = True  # Enable/disable rotating proxies

    # G2-specific selectors for JS-rendered content (updated for new UI)
    CATEGORIES_TABLE_SELECTOR = "//div[contains(@class, 'categories__table')]"
    CATEGORY_ROW_SELECTOR = "//div[contains(@class, 'categories__row')]"
    CATEGORY_LINK_SELECTOR = "//a[contains(@href, '/categories/')]"
    PAGE_NOT_FOUND_XPATH = "//h1[contains(text(),'404')]"

    # Selectors for subcategory detection and extraction
    SUBCATEGORY_SECTION_SELECTOR = "//div[contains(@class, 'paper') and contains(@class, 'paper--nestable')]"
    SUBCATEGORY_LINK_SELECTOR = "//div[contains(@class, 'paper')]//a[contains(@href, '/categories/')]"

    # Selectors for direct product listings (updated for new G2 UI)
    PRODUCT_LISTING_SECTION_SELECTOR = "//div[contains(text(), 'Listings in')] | //div[contains(text(), 'listings')]"
    PRODUCT_CARD_SELECTOR = "//div[contains(@class, 'segmented-shadow-card__segment')] | //div[contains(@class, 'product-card')]"

    async def start(self):
        for url in self.start_urls:
            yield Request(url, callback=self.parse)

    def parse(self, response):
        self.log.info(f"Parsing G2 category page: {response.url}")

        # Initialize browser driver for JS rendering
        self.init_driver(headless=False)

        try:
            # Navigate to the page and wait for JS to render
            title = self.navigate_to_page(response.url, wait_time=5)
            self.log.info(f"Page title: {title}")

            # Check if this is the main categories page
            if response.url == "https://www.g2.com/categories":
                yield from self.handle_main_categories_page(response)
            else:
                # Detect page type (subcategories vs direct products)
                page_type = self.detect_page_type()
                self.log.info(f"Detected page type: {page_type}")

                if page_type == "subcategories":
                    yield from self.handle_subcategories_page(response)
                elif page_type == "direct_products":
                    yield from self.handle_direct_products_page(response)
                else:
                    self.log.warning(f"Unknown page type for {response.url}")

        except Exception as e:
            self.log.error(f"Error in parse method: {str(e)}")

    def detect_page_type(self):
        # Detect if the current page has subcategories or direct product listings.
        # Wait for page content to load
        time.sleep(2)

        # Check for direct product listings first - look for the specific product card structure
        product_cards = self.find_elements_safe(
            "xpath", "//div[contains(@class, 'segmented-shadow-card__segment') and contains(@class, 'segmented-shadow-card__segment--multi-part')]", timeout=10)

        if product_cards:
            self.log.info(
                f"Found direct product listings with {len(product_cards)} product cards")
            return "direct_products"

        # If no product cards found, treat as subcategory page
        self.log.info("No product cards found, treating as subcategory page")
        return "subcategories"

    def handle_main_categories_page(self, response):
        # Handle the main categories page by extracting and randomly sampling category links.
        self.log.info("Handling main categories page")

        # Try multiple selectors to find category links
        category_links = self.find_elements_safe(
            "xpath", self.CATEGORY_LINK_SELECTOR)

        if not category_links:
            self.log.warning(
                "Primary selector failed, trying alternative selectors...")
            # Try alternative selectors
            category_links = self.find_elements_safe(
                "xpath", "//a[contains(@href, '/categories/')]")

            if not category_links:
                self.log.warning(
                    "Alternative selector also failed, trying broader search...")
                # Try even broader search
                category_links = self.find_elements_safe(
                    "xpath", "//a[contains(@href, '/categories/') and not(contains(@href, '?'))]")

        if not category_links:
            self.log.error(
                "No category links found on main categories page with any selector")
            # Log page structure for debugging
            try:
                page_text = self.driver.find_element(
                    By.TAG_NAME, "body").text[:1000]
                self.log.warning(f"Page content preview: {page_text}")
            except:
                pass
            return

        self.log.success(f"Found {len(category_links)} total category links")

        # Select from top 10 categories instead of random sampling
        if self.SAMPLE_CATEGORY_COUNT > 0:
            # Take top 10 categories and then sample from those
            top_10_links = category_links[:10]
            sampled_links = random.sample(top_10_links, min(
                self.SAMPLE_CATEGORY_COUNT, len(top_10_links)))
            self.log.info(
                f"Randomly sampled {len(sampled_links)} categories from top 10 categories")

            # Log the randomly selected categories
            for i, link in enumerate(sampled_links):
                try:
                    href = link.get_attribute("href")
                    name = link.text.strip()
                    display_name = name if name else href.split(
                        '/')[-1].replace('-', ' ').title()
                    self.log.info(
                        f"Selected category {i+1}: {display_name} -> {href}")
                except Exception as e:
                    self.log.warning(
                        f"Error examining selected link {i+1}: {str(e)}")
        else:
            # Use all categories
            sampled_links = category_links
            self.log.info(f"Using all {len(sampled_links)} categories")

        # Process sampled category links
        processed_count = 0
        for link in sampled_links:
            try:
                href = link.get_attribute("href")
                name = link.text.strip()

                self.log.info(
                    f"Processing category link: href={href}, name={name}")

                if href:  # Only check if href exists, name can be empty
                    full_url = urljoin(response.url, href)
                    # Use name if available, otherwise extract from URL
                    display_name = name if name else href.split(
                        '/')[-1].replace('-', ' ').title()
                    self.log.info(
                        f"Following category: {display_name} -> {full_url}")
                    yield Request(
                        full_url,
                        callback=self.parse,
                        meta={'category_name': display_name},
                        dont_filter=True
                    )
                    processed_count += 1
                    self.log.info(
                        f"Queued category {processed_count}/{len(sampled_links)}: {display_name}")
                else:
                    self.log.warning(
                        f"Invalid category link: href={href}, name={name}")
            except Exception as e:
                self.log.warning(
                    f"Error processing category link: {str(e)}")

        self.log.success(
            f"Successfully queued {processed_count} category requests")

    def handle_subcategories_page(self, response):
        # Handle a page that contains subcategories.
        self.log.info("Handling subcategories page")

        # Use the driver that's already initialized in parse method
        subcategory_links = self.find_elements_safe(
            "xpath", self.SUBCATEGORY_LINK_SELECTOR)

        if not subcategory_links:
            self.log.warning("No subcategory links found")
            return

        self.log.success(f"Found {len(subcategory_links)} subcategory links")

        # Extract and follow subcategory links
        processed_count = 0
        for link in subcategory_links:
            try:
                href = link.get_attribute("href")
                name = link.text.strip()

                self.log.info(
                    f"Processing subcategory link: href={href}, name={name}")

                if href and name:
                    full_url = urljoin(response.url, href)
                    self.log.info(
                        f"Following subcategory: {name} -> {full_url}")
                    yield Request(
                        full_url,
                        callback=self.parse_category,
                        meta={'page_num': 1, 'category_name': name},
                        dont_filter=True  # Ensure all subcategories get processed
                    )
                    processed_count += 1
                    self.log.info(
                        f"Queued subcategory {processed_count}/{len(subcategory_links)}: {name}")
                else:
                    self.log.warning(
                        f"Invalid subcategory link: href={href}, name={name}")
            except Exception as e:
                self.log.warning(
                    f"Error processing subcategory link: {str(e)}")

        self.log.success(
            f"Successfully queued {processed_count} subcategory requests")

    def handle_direct_products_page(self, response):
        # Handle a page that contains direct product listings.
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
        # Parses a category page to extract software listings.
        # selectors based on new G2 UI structure
        PRODUCT_CARD_SELECTOR = "//div[contains(@class, 'segmented-shadow-card__segment') and contains(@class, 'segmented-shadow-card__segment--multi-part')]"

        PRODUCT_NAME_SELECTOR = ".//div[@itemprop='name'] | .//div[contains(@class, 'product-card__product-name')]//div"
        PRODUCT_LINK_SELECTOR = ".//a[.//div[@itemprop='name']] | .//a[contains(@class, 'product-card__img')]"
        LOGO_SELECTOR = ".//img[@itemprop='image'] | .//img[contains(@class, 'x-deferred-image-initialized')]"
        DESCRIPTION_SELECTOR = ".//span[contains(@class, 'product-listing__paragraph')]"

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
                return

            self.log.success(
                f"Found {len(product_cards)} product listings on page.")

            # Collect all items first instead of yielding immediately
            collected_items = []
            scraped_count = 0

            for i, card in enumerate(product_cards):
                self.log.info(f"Processing card {i+1}/{len(product_cards)}")
                listing_data = self.extract_product_data(
                    card, category_slug, category_name, response.url,
                    PRODUCT_NAME_SELECTOR, PRODUCT_LINK_SELECTOR, LOGO_SELECTOR, DESCRIPTION_SELECTOR)
                if listing_data:
                    # Log concise info instead of full data
                    self.log.info(
                        f"Scraped: {listing_data.get('product_name', 'Unknown')} - {listing_data.get('category', {}).get('name', 'Unknown')}")
                    # Collect the item instead of yielding immediately
                    collected_items.append(listing_data)
                    scraped_count += 1
                else:
                    self.log.warning(f"Failed to extract data from card {i+1}")

            self.log.success(
                f"Successfully scraped {scraped_count} products from {len(product_cards)} cards")

            # Yield all collected items at once
            for item in collected_items:
                # Log each scraped product in JSON structure
                # self.log.info(
                #     f"Scraped product: {json.dumps(item, ensure_ascii=False)}")
                yield item

            # Handle pagination using URL-based approach
            next_request = self.handle_pagination(response, category_name)
            if next_request:
                yield next_request

        except Exception as e:
            self.log.error(f"Error in parse_category method: {str(e)}")

    def extract_category_info(self, url):
        # Extract category slug and name from URL
        path = urlparse(url).path
        # Assuming URL structure like /categories/crm
        category_slug = path.strip("/").split("/")[-1]
        category_name = category_slug.replace("-", " ").title()
        self.log.info(
            f"Extracted category info from {url}: slug={category_slug}, name={category_name}")
        return category_slug, category_name

    def extract_product_data(self, card, category_slug, category_name, base_url,
                             name_selector, link_selector, logo_selector, description_selector):
        # Extract core product data from a single product card

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
        # Extract complete product description using simplified CSS selector approach
        try:
            # Find description element using CSS selector instead of XPath
            desc_element = card.find_element(
                By.CSS_SELECTOR, "span.product-listing__paragraph")

            if desc_element:
                # Get small description (text inside span, excluding "Show More" link)
                small_description = desc_element.get_attribute(
                    "textContent").strip()
                if "Show More" in small_description:
                    small_description = small_description.split("Show More")[
                        0].strip()
                small_description = small_description.replace(
                    "...", "").strip()

                # Get extended description from data attribute
                extended_description = desc_element.get_attribute(
                    "data-truncate-revealer-overflow-text")

                if extended_description and small_description:
                    # Combine both parts
                    full_description = small_description + " " + extended_description
                    return " ".join(full_description.split())
                elif small_description:
                    # Only small description available
                    return " ".join(small_description.split())
                elif extended_description:
                    # Only extended description available (rare case)
                    return " ".join(extended_description.split())
                else:
                    return ""

            return ""

        except Exception as e:
            # Extract just the error message without stack trace
            error_msg = str(e).split('\n')[0] if '\n' in str(e) else str(e)
            self.log.warning(f"Failed to extract description: {error_msg}")
            return ""

    def handle_pagination(self, response, category_name):
        # Handle pagination logic for G2 using URL-based approach with ?page= parameter
        current_page = response.meta.get('page_num', 1)

        should_continue = False
        if self.SCRAPE_ALL_PAGES:
            should_continue = True
            limit_info = "all pages"
        else:
            should_continue = current_page < self.MAX_PAGES
            limit_info = f"max {self.MAX_PAGES} pages"

        if should_continue:
            # Construct next page URL by appending ?page= parameter
            # Remove existing query params
            base_url = response.url.split('?')[0]
            next_page_num = current_page + 1
            next_page_url = f"{base_url}?page={next_page_num}"

            self.log.info(
                f"Scraping next page ({next_page_num}) for category '{category_name}': {next_page_url}"
            )
            return Request(
                next_page_url,
                callback=self.parse_category,
                meta={'page_num': next_page_num,
                      'category_name': category_name}
            )

        self.log.success(
            f"Finished scraping category '{category_name}'. Reached limit ({limit_info})."
        )
        return None
