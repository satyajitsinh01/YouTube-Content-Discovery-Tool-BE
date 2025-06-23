from typing import List, Dict, Any
from app.services.llm_handler import LLMHandler
import json

class VideoFilter:
    def __init__(self, min_views: int = 100000, min_subscribers: int = 100000, allowed_countries: List[str] = None):
        self.min_views = min_views
        self.min_subscribers = min_subscribers
        self.allowed_countries = allowed_countries or ['US', 'GB', 'IN', "CA", "AU", "DE", "FR", "IT", "ES", "NL", "SE", "NO", "DK", "FI", "PL", "CZ", "RO", "HU", "BG", "HR", "SK", "SI", "EE", "LV", "LT", "IS", "NO", "SE", "DK", "FI", "PL", "CZ", "RO", "HU", "BG", "HR", "SK", "SI", "EE", "LV", "LT", "IS"]  # USA, UK, India
        self.llm_handler = LLMHandler()

    async def extract_email_and_links(self, description: str) -> Dict[str, Any]:
        """
        Extract email and useful links from channel description using LLM.
        """
        try:
            response = await self.llm_handler.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts contact information."},
                    {"role": "user", "content": f"Extract any email addresses and useful contact links from the following channel description. Return ONLY a JSON object with 'email' and 'contact_links' fields. If none found, return empty strings or arrays.\n\nDescription:\n{description}"}
                ],
                temperature=0.3,
                max_tokens=150,
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON string into a Python dictionary
            result = response.choices[0].message.content
            contact_info = json.loads(result)
            
            # Ensure email is always a string
            if isinstance(contact_info.get('email'), list) and len(contact_info.get('email', [])) > 0:
                contact_info['email'] = contact_info['email'][0]
            elif contact_info.get('email') is None or not isinstance(contact_info.get('email'), str):
                contact_info['email'] = ""
                
            # Ensure contact_links is always a list
            if not isinstance(contact_info.get('contact_links'), list):
                if contact_info.get('contact_links') and isinstance(contact_info.get('contact_links'), str):
                    contact_info['contact_links'] = [contact_info['contact_links']]
                else:
                    contact_info['contact_links'] = []
                    
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
        print("videos============", self.min_views, self.min_subscribers, self.allowed_countries)
        
        for video in videos:
            # Check view count
            if video['video_view_count'] < self.min_views:
                continue
                
            # Check subscriber count
            if video['channel_subscriber_count'] < self.min_subscribers:
                continue
                
            # Check country if available
            country = video.get('channel_country')
            if country and country not in self.allowed_countries:
                continue
            
            # Extract email and contact links from channel description
            contact_info = {"email": "", "contact_links": []}
            if video.get('channel_description'):
                contact_info = await self.extract_email_and_links(video.get('channel_description', ''))
            
            # Ensure email is a string
            email = contact_info.get('email', '')
            if isinstance(email, list) and len(email) > 0:
                email = email[0]
            elif not isinstance(email, str):
                email = ""
                
            # Ensure contact_links is a list
            contact_links = contact_info.get('contact_links', [])
            if not isinstance(contact_links, list):
                if contact_links and isinstance(contact_links, str):
                    contact_links = [contact_links]
                else:
                    contact_links = []
                
            # Transform data to match VideoResult model while keeping all additional data
            transformed_video = {
                # Required fields for VideoResult model
                'title': video['video_title'],
                'link': video['video_link'],
                'channel_name': video['channel_name'],
                'email': email,
                'contact_links': contact_links,
                'subscriber_count': video['channel_subscriber_count'],
                'view_count': video['video_view_count'],
                'country': video.get('channel_country'),
                
                # Additional video details
                'description': video.get('video_description'),
                'published_at': video.get('video_published_at'),
                'tags': video.get('video_tags', []),
                'category_id': video.get('video_category_id'),
                'duration': video.get('video_duration'),
                'definition': video.get('video_definition'),
                'caption_available': video.get('video_caption'),
                'licensed_content': video.get('video_licensed_content'),
                'projection': video.get('video_projection'),
                'topic_categories': video.get('video_topic_categories', []),
                'like_count': video.get('video_like_count'),
                'comment_count': video.get('video_comment_count'),
                
                # Additional channel details
                'channel_info': {
                    'description': video.get('channel_description'),
                    'custom_url': video.get('channel_custom_url'),
                    'published_at': video.get('channel_published_at'),
                    'default_language': video.get('channel_default_language'),
                    'keywords': video.get('channel_keywords'),
                    'video_count': video.get('channel_video_count'),
                    'total_views': video.get('channel_view_count'),
                    'hidden_subscriber_count': video.get('channel_hidden_subscriber_count'),
                }
            }
                
            filtered_videos.append(transformed_video)
            
        return filtered_videos 