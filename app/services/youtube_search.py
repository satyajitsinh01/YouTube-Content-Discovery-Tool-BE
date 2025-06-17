from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
import asyncio
from functools import partial

# Load environment variables from .env file
load_dotenv()

class YouTubeSearch:
    def __init__(self):
        """
        Initializes the YouTube Data API client.
        Requires a YOUTUBE_API_KEY environment variable to be set.
        """
        api_key = os.getenv('YOUTUBE_API_KEY')
        if not api_key:
            raise ValueError("YOUTUBE_API_KEY environment variable is not set. "
                             "Please create a .env file and add YOUTUBE_API_KEY='YOUR_API_KEY_HERE'.")
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        print("YouTube API client initialized successfully.")

    async def search_videos(self, query: str, max_results: int = 10000) -> List[Dict[str, Any]]:
        """
        Search for videos using the YouTube Data API and fetch comprehensive details
        about the video and its associated channel.

        Note: The YouTube Data API does NOT provide direct access to a channel's
        private business email address due to privacy policies. This method
        retrieves publicly available information.

        Args:
            query (str): The search term for videos.
            max_results (int): The maximum number of video results to retrieve (1-50).

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each containing
                                   comprehensive information about a video and its channel.
                                   Only includes one video per unique channel.
        """
        try:
            print(f"Searching for videos with query: '{query}' (Max results: {max_results})...")
            
            # Run the synchronous YouTube API calls in a thread pool
            loop = asyncio.get_event_loop()
            search_response = await loop.run_in_executor(
                None,
                partial(
                    self.youtube.search().list,
                    q=query,
                    part='id,snippet',
                    type='video',
                    maxResults=max_results
                )
            )
            search_response = await loop.run_in_executor(None, search_response.execute)

            videos_info = []
            seen_channel_ids = set()  # Track channel IDs we've already processed
            
            for item in search_response.get('items', []):
                try:
                    video_id = item['id']['videoId']
                    channel_id = item['snippet']['channelId']

                    # Skip this video if we've already seen this channel ID
                    if channel_id in seen_channel_ids:
                        print(f"Skipping video ID: {video_id} from duplicate channel ID: {channel_id}")
                        continue
                    
                    # Add this channel ID to our set of seen channels
                    seen_channel_ids.add(channel_id)
                    
                    print(f"Processing video ID: {video_id}, Channel ID: {channel_id}")

                    # --- Get Comprehensive Video Details ---
                    # Request more parts for detailed video information
                    video_request = self.youtube.videos().list(
                        part='snippet,contentDetails,statistics,topicDetails',
                        id=video_id
                    )
                    video_response = await loop.run_in_executor(None, video_request.execute)

                    video_data = video_response['items'][0] if video_response.get('items') else {}
                    video_snippet = video_data.get('snippet', {})
                    video_stats = video_data.get('statistics', {})
                    video_content_details = video_data.get('contentDetails', {})
                    video_topic_details = video_data.get('topicDetails', {})


                    # --- Get Comprehensive Channel Details ---
                    # Request more parts for detailed channel information
                    channel_request = self.youtube.channels().list(
                        part='snippet,statistics,brandingSettings',
                        id=channel_id
                    )
                    channel_response = await loop.run_in_executor(None, channel_request.execute)

                    channel_data = channel_response['items'][0] if channel_response.get('items') else {}
                    channel_snippet = channel_data.get('snippet', {})
                    channel_stats = channel_data.get('statistics', {})
                    channel_branding = channel_data.get('brandingSettings', {})


                    # Construct the dictionary for comprehensive video and channel information
                    video_detail_info = {
                        'video_title': video_snippet.get('title', 'N/A'),
                        'video_description': video_snippet.get('description', 'N/A'),
                        'video_link': f'https://www.youtube.com/watch?v={video_id}',
                        'video_published_at': video_snippet.get('publishedAt', 'N/A'),
                        'video_tags': video_snippet.get('tags', []),
                        'video_category_id': video_snippet.get('categoryId', 'N/A'),
                        'video_default_language': video_snippet.get('defaultLanguage', 'N/A'),
                        'video_duration': video_content_details.get('duration', 'N/A'), # ISO 8601 format
                        'video_definition': video_content_details.get('definition', 'N/A'), # e.g., 'hd', 'sd'
                        'video_caption': video_content_details.get('caption', 'N/A'), # 'true' or 'false'
                        'video_licensed_content': video_content_details.get('licensedContent', False),
                        'video_projection': video_content_details.get('projection', 'rectangular'),
                        'video_topic_categories': video_topic_details.get('topicCategories', []),

                        'video_view_count': int(video_stats.get('viewCount', 0)),
                        'video_like_count': int(video_stats.get('likeCount', 0)),
                        'video_dislike_count': int(video_stats.get('dislikeCount', 0)) if 'dislikeCount' in video_stats else 'Hidden', # Dislike count might be hidden
                        'video_comment_count': int(video_stats.get('commentCount', 0)),

                        'channel_name': channel_snippet.get('title', 'N/A'),
                        'channel_description': channel_snippet.get('description', 'N/A'),
                        'channel_custom_url': channel_snippet.get('customUrl', 'N/A'),
                        'channel_published_at': channel_snippet.get('publishedAt', 'N/A'),
                        'channel_country': channel_snippet.get('country', 'N/A'),
                        'channel_default_language': channel_branding.get('channel', {}).get('defaultLanguage', 'N/A'),
                        'channel_keywords': channel_branding.get('channel', {}).get('keywords', 'N/A'),

                        'channel_subscriber_count': int(channel_stats.get('subscriberCount', 0)),
                        'channel_video_count': int(channel_stats.get('videoCount', 0)),
                        'channel_view_count': int(channel_stats.get('viewCount', 0)),
                        'channel_hidden_subscriber_count': channel_stats.get('hiddenSubscriberCount', False),

                        # IMPORTANT: The YouTube Data API does NOT provide email addresses directly.
                        # Creators often list business emails in their channel's "About" section
                        # or on linked external websites/social media. This information cannot
                        # be programmatically retrieved via the official API.
                        'business_email_info': "Not available via YouTube Data API. Check channel's 'About' page or linked websites."
                    }
                    
                    videos_info.append(video_detail_info)
                except Exception as e:
                    print(f"Error processing item (Video ID: {item['id'].get('videoId', 'N/A')}, Channel ID: {item['snippet'].get('channelId', 'N/A')}): {e}. Skipping this item.")
                    continue # Continue to the next item if there's an error with one

            return videos_info

        except HttpError as e:
            print(f"YouTube API error: {str(e)}")
            raise Exception(f"YouTube API error: {str(e)}")
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            raise Exception(f"Unexpected error: {str(e)}")

