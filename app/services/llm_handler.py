import google.generativeai as genai
import os
from typing import List
from dotenv import load_dotenv
import json
import re

load_dotenv()

class LLMHandler:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')

    async def generate_synonyms(self, query: str) -> List[str]:
        """
        Generate related keywords/phrases using Gemini's model.
        """
        try:
            prompt = (
                "Generate 5 related search terms or phrases for YouTube content discovery.\n"
                f"Original query: {query}\n"
                "Requirements:\n"
                "- Each term should be relevant to the original query\n"
                "- Terms should be diverse but related\n"
                "- Keep each term concise (2-4 words)\n"
                "- Return only the 5 terms, one per line"
            )
            response = self.model.generate_content(prompt)
            related_terms = response.text.strip().split('\n')
            related_terms = [term.strip() for term in related_terms if term.strip()][:5]
            return related_terms
        except Exception as e:
            raise Exception(f"Error generating synonyms: {str(e)}")

    async def extract_contact_info(self, description: str) -> dict:
        """
        Extract email addresses and useful contact links from a channel description using Gemini.
        Returns a dict with 'email' and 'contact_links'.
        """
        try:
            prompt = (
                "Extract any email addresses and useful contact links from the following channel description. "
                "Return ONLY a JSON object with 'email' and 'contact_links' fields. "
                "If none found, return empty strings or arrays.\n\nDescription:\n" + description
            )
            response = self.model.generate_content(prompt)
            result = response.text.strip()
            # Remove Markdown code block (```json ... ```)
            match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", result)
            if match:
                result = match.group(1).strip()
            contact_info = json.loads(result)
            return contact_info
        except Exception as e:
            print(f"Error in extract_contact_info: {str(e)}")
            return {"email": "", "contact_links": []}

    async def __del__(self):
        if hasattr(self, 'client') and hasattr(self.client, 'aclose'):
            await self.client.aclose() 