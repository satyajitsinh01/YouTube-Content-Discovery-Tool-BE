from openai import AsyncOpenAI
import os
from typing import List
from dotenv import load_dotenv
import httpx

load_dotenv()

class LLMHandler:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        # Initialize with a custom httpx client to avoid proxy issues
        self.client = AsyncOpenAI(
            api_key=api_key,
            http_client=httpx.AsyncClient()
        )

    async def generate_synonyms(self, query: str) -> List[str]:
        """
        Generate related keywords/phrases using OpenAI's GPT model.
        """
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates related search terms for content discovery."},
                    {"role": "user", "content": f"Generate 5 related search terms or phrases for YouTube content discovery.\nOriginal query: {query}\nRequirements:\n- Each term should be relevant to the original query\n- Terms should be diverse but related\n- Keep each term concise (2-4 words)\n- Return only the 5 terms, one per line"}
                ],
                temperature=0.7,
                max_tokens=150
            )

            # Extract and clean the related terms
            related_terms = response.choices[0].message.content.strip().split('\n')
            # Clean and take only the first 5 terms
            related_terms = [term.strip() for term in related_terms if term.strip()][:5]

            return related_terms

        except Exception as e:
            raise Exception(f"Error generating synonyms: {str(e)}")

    async def __del__(self):
        if hasattr(self, 'client') and hasattr(self.client, 'aclose'):
            await self.client.aclose() 