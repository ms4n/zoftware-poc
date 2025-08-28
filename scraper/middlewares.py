import csv
import random
from loguru import logger


class RotatingProxyMiddleware:
    def __init__(self):
        self.proxies = self._load_proxies()

    def _load_proxies(self):
        proxies = []
        try:
            with open("scraper/proxies_formatted.csv", "r") as f:
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
            logger.info(f"Loaded {len(proxies)} proxies.")
        except FileNotFoundError:
            logger.warning("Proxy file not found. Scraping without proxies.")
        return proxies

    def process_request(self, request, spider):
        if self.proxies and "playwright" in request.meta:
            proxy = random.choice(self.proxies)
            proxy_server = f"http://{proxy['host']}:{proxy['port']}"

            proxy_settings = {
                "server": proxy_server,
                "username": proxy["user"],
                "password": proxy["pass"],
            }

            # Start with global settings, then add per-request options, then add proxy
            launch_options = spider.settings.get(
                "PLAYWRIGHT_LAUNCH_OPTIONS", {}).copy()
            launch_options.update(request.meta.get(
                "playwright_launch_options", {}))
            launch_options["proxy"] = proxy_settings
            request.meta["playwright_launch_options"] = launch_options

            spider.logger.warning(
                f"DEBUG: Applied proxy {proxy['host']}:{proxy['port']} to request {request.url}")
            spider.logger.warning(f"DEBUG: Launch options: {launch_options}")
        else:
            spider.logger.warning(
                f"DEBUG: No proxy applied to request {request.url}")
