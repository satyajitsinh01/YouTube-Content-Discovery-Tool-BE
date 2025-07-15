from typing import List, Dict, Any
from services.llm_handler import LLMHandler
import json
from pydantic import BaseModel


class VideoUrl(BaseModel):
    id: str
    url: str
    isicp: bool = False  # Default value


class VideoFilter:
    def __init__(
        self,
        min_views: int = 100000,
        min_subscribers: int = 100000,
        allowed_countries: List[str] = None,
    ):
        self.min_views = min_views
        self.min_subscribers = min_subscribers
        print(f"DEBUG: VideoFilter received allowed_countries: {allowed_countries}")
        self.allowed_countries = allowed_countries or [
            "US",
            "GB",
            "IN",
            "CA",
            "AU",
            "DE",
            "FR",
            "IT",
            "ES",
            "NL",
            "SE",
            "NO",
            "DK",
            "FI",
            "PL",
            "CZ",
            "RO",
            "HU",
            "BG",
            "HR",
            "SK",
            "SI",
            "EE",
            "LV",
            "LT",
            "IS",
            "NO",
            "SE",
            "DK",
            "FI",
            "PL",
            "CZ",
            "RO",
            "HU",
            "BG",
            "HR",
            "SK",
            "SI",
            "EE",
            "LV",
            "LT",
            "IS",
        ]  # USA, UK, India
        print(f"DEBUG: VideoFilter final allowed_countries: {self.allowed_countries}")
        self.llm_handler = LLMHandler()

    async def extract_email_and_links(
        self, description: str, channel_details: dict
    ) -> Dict[str, Any]:
        """
        Extract email and useful links from channel description using LLM.
        """
        try:
            contact_info = await self.llm_handler.extract_contact_info(
                description, channel_details
            )
            print("contact_info", contact_info)

            # Ensure email is always a string
            if (
                isinstance(contact_info.get("email"), list)
                and len(contact_info.get("email", [])) > 0
            ):
                contact_info["email"] = contact_info["email"][0]
            elif contact_info.get("email") is None or not isinstance(
                contact_info.get("email"), str
            ):
                contact_info["email"] = ""

            # Ensure contact_links is always a list
            if not isinstance(contact_info.get("contact_links"), list):
                if contact_info.get("contact_links") and isinstance(
                    contact_info.get("contact_links"), str
                ):
                    contact_info["contact_links"] = [contact_info["contact_links"]]
                else:
                    contact_info["contact_links"] = []

            return contact_info
        except Exception as e:
            print(f"Error extracting email and links: {str(e)}")
            return {"email": "", "contact_links": []}

    async def filter_videos(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter videos based on view count, subscriber count, and country criteria.
        Transform data to match VideoResult model format while preserving all additional data.
        """
        filtered_videos = []
        print(
            "videos============",
            self.min_views,
            self.min_subscribers,
            self.allowed_countries,
        )

        for video in videos:
            # Check view count
            if video.get("video_view_count", 0) < self.min_views:
                continue

            # Check subscriber count
            if video.get("channel_subscriber_count", 0) < self.min_subscribers:
                continue

            # Check country if available
            country = video.get("channel_country")
            if country and country not in self.allowed_countries:
                continue

            # Extract email and contact links from channel description
            contact_info = {"email": "", "contact_links": []}
            if video.get("channel_name"):
                # Build a detailed string with all relevant info
                channel_data_str = (
                    f"Channel Name: {video.get('channel_name', '')}\n"
                    f"Subscribers: {video.get('channel_subscriber_count', '')}\n"
                    f"About: {video.get('channel_description', '')}\n"
                    f"Links: {', '.join(video.get('channel_links', [])) if video.get('channel_links') else ''}\n"
                    f"Last 3 Video Titles: {', '.join(video.get('last_3_video_titles', [])) if video.get('last_3_video_titles') else ''}\n"
                    f"Average Views (Last 3 Videos): {video.get('avg_views_last_3', '')}\n"
                    f"Last 3 Video Descriptions: {', '.join(video.get('last_3_video_descriptions', [])) if video.get('last_3_video_descriptions') else ''}\n"
                    f"Country: {video.get('channel_country', '')}\n"
                    f"Channel Description: {video.get('channel_description', '')}"
                )
                contact_info = await self.extract_email_and_links(
                    video.get("channel_description", ""), channel_data_str
                )

            # Ensure email is a string
            email = contact_info.get("email", "")
            if isinstance(email, list) and len(email) > 0:
                email = email[0]
            elif not isinstance(email, str):
                email = ""

            # Ensure contact_links is a list
            contact_links = contact_info.get("contact_links", [])
            if not isinstance(contact_links, list):
                if contact_links and isinstance(contact_links, str):
                    contact_links = [contact_links]
                else:
                    contact_links = []

            # Get video ID to ensure we can create a link if missing
            video_id = video.get("video_id", "")
            if not video_id and "video_link" in video:
                # Try to extract video ID from link if available
                link = video.get("video_link", "")
                if "watch?v=" in link:
                    video_id = link.split("watch?v=")[-1].split("&")[0]

            # Ensure we have a valid link
            video_link = video.get("video_link", "")
            if not video_link and video_id:
                video_link = f"https://www.youtube.com/watch?v={video_id}"
            elif not video_link:
                # If we can't determine the link, use a placeholder
                video_link = "https://www.youtube.com/"
            print("video", video)
            # Transform data to match VideoResult model while keeping all additional data
            transformed_video = {
                # Required fields for VideoResult model
                "title": video.get("video_title", "N/A"),
                "link": video.get("video_link", "N/A"),  # Use our guaranteed link
                "channel_name": video.get("channel_name", "N/A"),
                "email": email if email else "N/A",
                "contact_links": contact_links if contact_links else [],
                "subscriber_count": video.get("channel_subscriber_count", 0),
                "view_count": video.get("video_view_count", 0),
                "country": video.get("channel_country", "N/A"),
                # Additional video details
                "description": video.get("video_description"),
                "published_at": video.get("video_published_at"),
                "tags": video.get("video_tags", []),
                "category_id": video.get("video_category_id"),
                "duration": video.get("video_duration"),
                "definition": video.get("video_definition"),
                "caption_available": video.get("video_caption"),
                "licensed_content": video.get("video_licensed_content"),
                "projection": video.get("video_projection"),
                "topic_categories": video.get("video_topic_categories", []),
                "like_count": video.get("video_like_count"),
                "comment_count": video.get("video_comment_count"),
                "isicp": contact_info.get("isicp", False),
                # Additional channel details
                "channel_info": {
                    "description": video.get("channel_description"),
                    "custom_url": video.get("channel_custom_url"),
                    "published_at": video.get("channel_published_at"),
                    "default_language": video.get("channel_default_language"),
                    "keywords": video.get("channel_keywords"),
                    "video_count": video.get("channel_video_count"),
                    "total_views": video.get("channel_view_count"),
                    "hidden_subscriber_count": video.get(
                        "channel_hidden_subscriber_count"
                    ),
                },
            }

            filtered_videos.append(transformed_video)

        return filtered_videos
