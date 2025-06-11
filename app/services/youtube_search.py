from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class YouTubeSearch:
    def __init__(self):
        api_key = os.getenv('YOUTUBE_API_KEY')
        if not api_key:
            raise ValueError("YOUTUBE_API_KEY environment variable is not set")
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    async def search_videos(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for videos using the YouTube Data API and fetch additional details.
        """
        try:
            # Search for videos
            search_response = self.youtube.search().list(
                q=query,
                part='id,snippet',
                type='video',
                maxResults=10
            ).execute()

            videos = []
            for item in search_response.get('items', []):
                try:
                    video_id = item['id']['videoId']
                    
                    # Get video statistics
                    video_response = self.youtube.videos().list(
                        part='statistics',
                        id=video_id
                    ).execute()

                    if not video_response.get('items'):
                        continue

                    video_stats = video_response['items'][0]['statistics']
                    channel_id = item['snippet']['channelId']

                    # Get channel details
                    channel_response = self.youtube.channels().list(
                        part='snippet,statistics',
                        id=channel_id
                    ).execute()

                    if not channel_response.get('items'):
                        continue

                    channel_data = channel_response['items'][0]
                    
                    video_info = {
                        'title': item['snippet']['title'],
                        'link': f'https://www.youtube.com/watch?v={video_id}',
                        'channel_name': channel_data['snippet']['title'],
                        'subscriber_count': int(channel_data['statistics'].get('subscriberCount', 0)),
                        'view_count': int(video_stats.get('viewCount', 0)),
                        'country': channel_data['snippet'].get('country')
                    }
                    
                    videos.append(video_info)
                except Exception as e:
                    # Skip this video if there's an error processing it
                    continue

            return videos

        except HttpError as e:
            raise Exception(f"YouTube API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}") 