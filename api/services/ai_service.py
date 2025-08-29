from openai import OpenAI
import os
import time
from typing import Dict, Any, List, Optional
from loguru import logger
from schemas.product import ProductCategory
from dotenv import load_dotenv
from config.ai_config import get_ai_config, get_batch_config

# Load environment variables from .env file in api directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


class AIService:
    def __init__(self):
        # Get API key from environment variable
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")

        # Set OpenAI client
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None

        # Load configurations
        self.ai_config = get_ai_config()
        self.batch_config = get_batch_config()

        # Rate limiting
        self.last_request_time = 0
        self.requests_this_minute = 0
        self.minute_start_time = time.time()

    def _check_rate_limit(self):
        """Check and enforce rate limits"""
        current_time = time.time()

        # Reset counter if a minute has passed
        if current_time - self.minute_start_time >= 60:
            self.requests_this_minute = 0
            self.minute_start_time = current_time

        # Check if we've hit the rate limit
        if self.requests_this_minute >= self.batch_config["max_requests_per_minute"]:
            wait_time = 60 - (current_time - self.minute_start_time)
            if wait_time > 0:
                logger.info(
                    f"Rate limit reached, waiting {wait_time:.1f} seconds")
                time.sleep(wait_time)
                self.requests_this_minute = 0
                self.minute_start_time = time.time()

    def _make_api_request(self, messages: List[Dict[str, Any]], max_tokens: int = None) -> Dict[str, Any]:
        """Make API request with rate limiting"""
        self._check_rate_limit()

        # Use configured max_tokens if not specified
        if max_tokens is None:
            max_tokens = self.ai_config["max_tokens"]

        response = self.client.chat.completions.create(
            model=self.ai_config["model"],
            messages=messages,
            response_format=self.ai_config["response_format"],
            max_tokens=max_tokens,
            temperature=self.ai_config["temperature"]
        )

        # Update rate limiting counters
        self.requests_this_minute += 1
        self.last_request_time = time.time()

        return response

    def process_product(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process raw product data using OpenAI API with structured outputs
        Returns: description, category
        """
        if not self.api_key or not self.client:
            logger.error("OpenAI API key not available")
            raise Exception("OpenAI API key not configured")

        try:
            # Call OpenAI API with structured output
            messages = [
                {
                    "role": "system",
                    "content": "You are a software categorization expert. Analyze the product description and categorize it into one of the predefined categories. Create exactly 2 sentences for the description - no more, no less."
                },
                {
                    "role": "user",
                    "content": self._create_prompt(raw_data)
                }
            ]

            response = self._make_api_request(messages, max_tokens=500)

            # Parse the response
            content = response.choices[0].message.content
            import json
            result = json.loads(content)

            # Validate required fields
            required_fields = ["description", "category"]
            for field in required_fields:
                if field not in result:
                    raise Exception(f"Missing required field: {field}")

            # Validate category
            try:
                category = ProductCategory(result["category"])
            except ValueError:
                logger.warning(
                    f"Invalid category '{result['category']}', defaulting to 'other'")
                category = ProductCategory.OTHER

            final_result = {
                "description": result["description"],
                "category": category.value
            }

            logger.info(
                f"Successfully processed product: {raw_data.get('name', 'Unknown')}")
            return final_result

        except Exception as e:
            logger.error(f"AI processing failed: {e}")
            raise Exception(f"AI processing failed: {str(e)}")

    def process_multiple_products(self, products_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process multiple products in a single AI request to reduce API calls
        Returns: List of results with product_id, description, category
        """
        if not self.api_key or not self.client:
            logger.error("OpenAI API key not available")
            raise Exception("OpenAI API key not configured")

        if not products_data:
            return []

        try:
            # Create a single prompt for all products
            combined_prompt = self._create_batch_prompt(products_data)

            logger.info(
                f"Processing {len(products_data)} products in single AI request")

            # Call OpenAI API with structured output for multiple products
            messages = [
                {
                    "role": "system",
                    "content": "You are a software categorization expert. Analyze multiple products and categorize each one. For each product, create exactly 2 sentences for the description - no more, no less."
                },
                {
                    "role": "user",
                    "content": combined_prompt
                }
            ]

            response = self._make_api_request(messages, max_tokens=2000)

            # Parse the response
            content = response.choices[0].message.content
            import json
            result = json.loads(content)

            # Validate and process results
            processed_results = []
            for i, product_data in enumerate(products_data):
                product_id = product_data.get("id")
                product_name = product_data.get("name", "Unknown")

                try:
                    # Extract result for this product
                    if "products" in result and i < len(result["products"]):
                        product_result = result["products"][i]
                    else:
                        # Fallback: try to find by name
                        product_result = self._find_product_result(
                            result, product_name)

                    if product_result and "description" in product_result and "category" in product_result:
                        # Validate category
                        try:
                            category = ProductCategory(
                                product_result["category"])
                        except ValueError:
                            logger.warning(
                                f"Invalid category '{product_result['category']}' for {product_name}, defaulting to 'other'")
                            category = ProductCategory.OTHER

                        processed_results.append({
                            "product_id": product_id,
                            "description": product_result["description"],
                            "category": category.value
                        })

                        logger.info(f"Successfully processed: {product_name}")
                    else:
                        logger.warning(
                            f"Missing required fields for {product_name}")
                        # Add default result
                        processed_results.append({
                            "product_id": product_id,
                            "description": f"{product_name} is a software product that provides various features and functionality.",
                            "category": "other"
                        })

                except Exception as e:
                    logger.error(f"Error processing {product_name}: {e}")
                    # Add default result on error
                    processed_results.append({
                        "product_id": product_id,
                        "description": f"{product_name} is a software product that provides various features and functionality.",
                        "category": "other"
                    })

            logger.info(
                f"Successfully processed {len(processed_results)} out of {len(products_data)} products")
            return processed_results

        except Exception as e:
            logger.error(f"AI batch processing failed: {e}")
            # Return default results for all products on failure
            default_results = []
            for product_data in products_data:
                product_id = product_data.get("id")
                product_name = product_data.get("name", "Unknown")
                default_results.append({
                    "product_id": product_id,
                    "description": f"{product_name} is a software product that provides various features and functionality.",
                    "category": "other"
                })
            return default_results

    def _find_product_result(self, result: Dict[str, Any], product_name: str) -> Optional[Dict[str, Any]]:
        """Find product result by name in case the order doesn't match"""
        if "products" in result:
            for product_result in result["products"]:
                if product_result.get("name") == product_name:
                    return product_result
        return None

    def _create_batch_prompt(self, products_data: List[Dict[str, Any]]) -> str:
        """Create a prompt for processing multiple products at once"""
        prompt = "Please analyze the following software products and provide a JSON response with the following structure:\n\n"
        prompt += "{\n"
        prompt += '  "products": [\n'

        for i, product in enumerate(products_data):
            name = product.get('name', 'Unknown Product')
            description = product.get(
                'description', 'No description available')
            category = product.get('category', 'No category')
            website = product.get('website', 'No website')

            prompt += '    {\n'
            prompt += f'      "name": "{name}",\n'
            prompt += f'      "description": "EXACTLY 2 sentences - no more, no less. Make it professional and clear while preserving important context.",\n'
            prompt += f'      "category": "Choose from: sales_marketing, devtools, data_analytics, productivity, finance, other"\n'
            prompt += '    }'
            if i < len(products_data) - 1:
                prompt += ','
            prompt += '\n'

        prompt += '  ]\n'
        prompt += '}\n\n'
        prompt += 'Product details:\n'

        for product in products_data:
            name = product.get('name', 'Unknown Product')
            description = product.get(
                'description', 'No description available')
            category = product.get('category', 'No category')
            website = product.get('website', 'No website')

            prompt += f'\nProduct Name: {name}\n'
            prompt += f'Website: {website}\n'
            prompt += f'Raw Category: {category}\n'
            prompt += f'Raw Description: {description}\n'

        prompt += '\nIMPORTANT: The description must be exactly 2 sentences. Do not truncate or add ellipsis.'
        prompt += ' If the product doesn\'t fit clearly into the first 5 categories, use "other".'

        return prompt

    def _create_prompt(self, raw_data: Dict[str, Any]) -> str:
        """Create the prompt for OpenAI API for single product"""
        name = raw_data.get('name', 'Unknown Product')
        description = raw_data.get('description', 'No description available')
        category = raw_data.get('category', 'No category')
        website = raw_data.get('website', 'No website')

        prompt = f"""
        Product Name: {name}
        Website: {website}
        Raw Category: {category}
        Raw Description: {description}

        Please analyze this software product and provide a JSON response with:
        1. description: EXACTLY 2 sentences - no more, no less. Make it professional and clear while preserving important context.
        2. category: Choose from: sales_marketing, devtools, data_analytics, productivity, finance, other

        If the product doesn't fit clearly into the first 5 categories, use "other".
        IMPORTANT: The description must be exactly 2 sentences. Do not truncate or add ellipsis.
        """

        return prompt.strip()
