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
        self.model = genai.GenerativeModel("gemini-2.5-pro")

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
            related_terms = response.text.strip().split("\n")
            related_terms = [term.strip() for term in related_terms if term.strip()][:1]
            return related_terms
        except Exception as e:
            raise Exception(f"Error generating synonyms: {str(e)}")

    async def extract_contact_info(self, description: str, channel_details: dict) -> dict:
        """
        Extract email addresses and useful contact links from a channel description using Gemini.
        Returns a dict with 'email', 'contact_links', and 'isicp'.
        """
        try:
            # Build a formatted string from channel_details
            channel_name = channel_details.get('channel_name', '')
            sub_count = channel_details.get('sub_count', '')
            about = channel_details.get('about', '')
            links = channel_details.get('links', [])
            last_3_titles = channel_details.get('last_3_titles', [])
            avg_views = channel_details.get('avg_views', '')
            last_3_descriptions = channel_details.get('last_3_descriptions', [])
            country = channel_details.get('country', '')

            channel_data_str = (
                f"Channel Name: {channel_name}\n"
                f"Subscribers: {sub_count}\n"
                f"About: {about}\n"
                f"Links: {', '.join(links) if links else ''}\n"
                f"Last 3 Video Titles: {', '.join(last_3_titles) if last_3_titles else ''}\n"
                f"Average Views (Last 3 Videos): {avg_views}\n"
                f"Last 3 Video Descriptions: {', '.join(last_3_descriptions) if last_3_descriptions else ''}\n"
                f"Country: {country}\n"
                f"Channel Description: {description}"
            )

            prompt = (
                "You will be given YouTube channel data, and your task is to analyze whether the channel falls under our ICP (Ideal Customer Profile).\n\n"
                "Here is what you will be provided:\n"
                "- Channel name\n"
                "- Sub count\n"
                "- About me and all the links\n"
                "- Last 3 video titles and their average views\n"
                "- Last 3 video descriptions\n"
                "- Country\n\n"
                "Context:\n"
                "We run a creative agency that produces premium 3D videos for YouTubers who make storytelling and educational content. "
                "For example, imagine a video on how Rome was built — we use 3D to visualize things that don't have real footage. "
                "Another example: a 3D simulation of what it would feel like to be in the Twin Towers during 9/11. "
                "3D visuals help them go beyond stock footage or current AI visuals, which often look generic or lack creative control. "
                "We help them create a consistent and premium visual brand using high-quality 3D.\n\n"
                "Our ICP:\n"
                "- YouTubers who create educational, documentary, or narration-driven storytelling videos\n"
                "- Upload at least once per month\n"
                "- Long-form videos focused on watch time\n"
                "- Common niches:\n"
                "    - Explainers\n"
                "    - True crime / mystery\n"
                "    - History / politics\n"
                "    - Documentaries\n"
                "    - Science / space\n"
                "    - Nature / geo\n"
                "    - Tech / innovation\n"
                "    - Finance / business\n"
                "    - 3D animated videos\n"
                "- Sub count ideally 100K+, but smaller creators with strong content and good views may still qualify (flag as 'potential ICP')\n"
                "- Last 3 video average views should ideally be above 200K (lower is okay if other criteria are strong)\n"
                "- Channels with sponsor links or Patreon may be high-ticket clients\n"
                "- Ignore channels based in India\n\n"
                "Task:\n"
                "- Extract any email addresses and useful contact links from the description.\n"
                "- Return ONLY a JSON object with the following keys:\n"
                "  - 'email': extracted email or empty string\n"
                "  - 'contact_links': list of social or business-related links\n"
                "  - 'isicp': true/false depending on whether the channel meets our ICP\n"
                "  - 'why': a short reason why you think it fits or not\n"
                "  - 'high_ticket': true/false depending on sponsorships, Patreon, and strong views\n"
                "  - 'potential_icp': true/false if the channel doesn't fully meet criteria but has strong potential\n"
                "- Do not return any extra explanation — only the JSON.\n\n"
                "Here is the channel data:\n"
                f"{channel_data_str}"
            )
            response = self.model.generate_content(prompt)
            result = response.text.strip()
            # Remove Markdown code block (```json ... ```)
      
            try:
                # Try to extract JSON from code block, else fallback to first {...}
                match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", result)
                if match:
                    json_str = match.group(1).strip()
                else:
                    # Fallback: find first {...}
                    json_match = re.search(r"(\{[\s\S]+\})", result)
                    json_str = json_match.group(1).strip() if json_match else result

                contact_info = json.loads(json_str)
                # Set defaults for all expected keys
                defaults = {
                    "email": "",
                    "contact_links": [],
                    "isicp": False,
                    "why": "",
                    "high_ticket": False,
                    "potential_icp": False
                }
                for key, value in defaults.items():
                    contact_info.setdefault(key, value)
                return contact_info
            except Exception as e:
                print(f"Error in extract_contact_info: {str(e)}")
                return {"email": "", "contact_links": [], "isicp": False}
        except Exception as e:
            print(f"Error in extract_contact_info: {str(e)}")
            return {"email": "", "contact_links": [], "isicp": False}

    async def __del__(self):
        if hasattr(self, "client") and hasattr(self.client, "aclose"):
            await self.client.aclose()
