import scrapy
from loguru import logger
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from scraper.utils.proxy import ProxyManager


class BaseSpider(scrapy.Spider):
    """
    Base spider for all site-specific spiders.
    Provides common functionalities like Chrome driver management and logging.
    """

    def __init__(self, *args, **kwargs):
        super(BaseSpider, self).__init__(*args, **kwargs)
        self.setup_logging()
        self.driver = None
        self.wait = None
        self.proxy_manager = ProxyManager()

        # Initialize proxies if USE_ROTATING_PROXIES is enabled
        if getattr(self, 'USE_ROTATING_PROXIES', False):
            self.proxy_manager.load_proxies()

    def setup_logging(self):
        """Sets up Loguru logger."""
        logger.add(
            f"logs/{self.name}.log",
            rotation="500 MB",
            retention="10 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        )
        self.log = logger

    def get_random_proxy(self):
        """Get a random proxy from the proxy manager"""
        if hasattr(self, 'USE_ROTATING_PROXIES') and self.USE_ROTATING_PROXIES:
            return self.proxy_manager.get_random_proxy()
        return None

    def init_driver(self, headless=False, use_proxy=True):
        """Initialize undetected Chrome driver with configurable options"""
        if not self.driver:
            options = uc.ChromeOptions()

            if headless:
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1920,1080')

            # Add anti-detection options
            options.add_argument(
                '--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-extensions-except')
            options.add_argument('--disable-plugins-discovery')
            options.add_argument('--disable-default-apps')

            # Add proxy configuration if enabled and available
            if use_proxy:
                proxy = self.get_random_proxy()
                if proxy:
                    # Use simple proxy - Chrome will prompt for credentials
                    proxy_server = f"http://{proxy['host']}:{proxy['port']}"
                    options.add_argument(f'--proxy-server={proxy_server}')
                    self.log.info(
                        f"Using proxy: {proxy['host']}:{proxy['port']} (Chrome will prompt for credentials)")

            self.driver = uc.Chrome(options=options, use_subprocess=False)
            self.wait = WebDriverWait(self.driver, 10)
            self.log.info("Initialized undetected Chrome driver")

    def navigate_to_page(self, url, wait_time=3):
        """Navigate to a page and wait for it to load"""
        self.driver.get(url)
        time.sleep(wait_time)
        return self.driver.title

    def find_elements_safe(self, locator_type, locator_value, timeout=10):
        """Safely find elements with timeout and error handling"""
        try:
            if locator_type == "xpath":
                return self.wait.until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, locator_value))
                )
            elif locator_type == "class":
                return self.wait.until(
                    EC.presence_of_all_elements_located(
                        (By.CLASS_NAME, locator_value))
                )
            elif locator_type == "id":
                return self.wait.until(
                    EC.presence_of_all_elements_located((By.ID, locator_value))
                )
        except TimeoutException:
            return []

    def extract_text_safe(self, element, xpath):
        """Safely extract text from an element using xpath"""
        try:
            target_element = element.find_element(By.XPATH, xpath)
            return target_element.text.strip()
        except NoSuchElementException:
            return ""

    def extract_attribute_safe(self, element, xpath, attribute):
        """Safely extract an attribute from an element using xpath"""
        try:
            target_element = element.find_element(By.XPATH, xpath)
            return target_element.get_attribute(attribute)
        except NoSuchElementException:
            return ""

    def closed(self, reason):
        """Close the driver when spider is done"""
        if self.driver:
            self.driver.quit()
            self.log.info("Closed undetected Chrome driver")
