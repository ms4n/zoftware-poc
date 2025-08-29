from openai import OpenAI
import os
from typing import Dict, Any
from loguru import logger
from schemas.product import ProductCategory


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
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a software categorization expert. Analyze the product description and categorize it into one of the predefined categories. Create exactly 2 sentences for the description - no more, no less."
                    },
                    {
                        "role": "user",
                        "content": self._create_prompt(raw_data)
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=500,
                temperature=0.3
            )

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

    def _create_prompt(self, raw_data: Dict[str, Any]) -> str:
        """Create the prompt for OpenAI API"""
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
