import scrapy
from scrapy_playwright.page import PageMethod
from loguru import logger


class BaseSpider(scrapy.Spider):
    """
    Base spider for all site-specific spiders.
    It provides common functionalities like Playwright integration and logging.
    """

    def __init__(self, *args, **kwargs):
        super(BaseSpider, self).__init__(*args, **kwargs)
        self.setup_logging()

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

    async def start(self):
        """
        Must be implemented by subclasses to define the initial requests.
        """
        raise NotImplementedError

    def get_page_methods(self):
        """
        Returns a list of Playwright PageMethods to be used in requests.
        This can be extended by subclasses if more complex interactions are needed.
        """
        return [
            PageMethod("wait_for_load_state", "networkidle"),
        ]
