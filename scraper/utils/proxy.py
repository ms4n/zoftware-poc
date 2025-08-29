import csv
import random
from loguru import logger


class ProxyManager:
    """Manages proxy loading and rotation for web scraping"""

    def __init__(self, proxy_file_path="scraper/proxies_formatted.csv"):
        self.proxy_file_path = proxy_file_path
        self.proxies = []

    def load_proxies(self):
        """Load proxies from CSV file"""
        proxies = []
        try:
            with open(self.proxy_file_path, "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) == 4:
                        proxy_data = {
                            "host": row[0],
                            "port": row[1],
                            "user": row[2],
                            "pass": row[3],
                        }
                        proxies.append(proxy_data)

            logger.info(f"Loaded {len(proxies)} proxies for rotation.")

        except FileNotFoundError:
            logger.warning(
                f"Proxy file not found at {self.proxy_file_path}. Scraping without proxies.")

        self.proxies = proxies
        return proxies

    def get_random_proxy(self):
        """Get a random proxy from the loaded list"""
        if not self.proxies:
            return None
        return random.choice(self.proxies)

    def get_proxy_count(self):
        """Get the number of loaded proxies"""
        return len(self.proxies)

    def is_enabled(self):
        """Check if proxies are available"""
        return len(self.proxies) > 0
