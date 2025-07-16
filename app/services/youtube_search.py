from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
import asyncio
from functools import partial
import json
# Load environment variables from .env file
load_dotenv()
# Use the new ChannelScraper for email and link extraction
from app.services.channel_scraper import ChannelScraper

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

    async def search_videos(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for channels using the YouTube Data API and fetch up to `limit` channels using pagination.
        Uses a single ChannelScraper instance for all link/email extraction in this batch.
        """
        try:
            print(f"Searching for channels with query: '{query}' (Limit: {limit})...")
            loop = asyncio.get_event_loop()
            channels_info = []
            seen_channel_ids = set()
            next_page_token = None
            fetched = 0
            # Initialize ChannelScraper once for this batch
            # scraper = ChannelScraper()
            while fetched < limit:
                max_results = min(50, limit - fetched)  # YouTube API max is 50 per call
                search_params = {
                    'q': query,
                    'part': 'id,snippet',
                    'type': 'channel',
                    'maxResults': max_results
                }
                if next_page_token:
                    search_params['pageToken'] = next_page_token

                search_response = await loop.run_in_executor(
                    None,
                    partial(self.youtube.search().list, **search_params)
                )
                search_response = await loop.run_in_executor(None, search_response.execute)
            

                for item in search_response.get('items', []):
                    # Defensive: Only process if 'channelId' exists
                    if 'id' in item and 'channelId' in item['id']:
                        channel_id = item['id']['channelId']
                    else:
                     
                        continue
                    if channel_id in seen_channel_ids:
                        continue
                    seen_channel_ids.add(channel_id)
               
                    # --- Get Comprehensive Channel Details ---
                    channel_request = self.youtube.channels().list(
                        part='snippet,statistics,brandingSettings',
                        id=channel_id
                    )
                    channel_response = await loop.run_in_executor(None, channel_request.execute)
                    channel_data = channel_response['items'][0] if channel_response.get('items') else {}
                    channel_snippet = channel_data.get('snippet', {})
                    channel_stats = channel_data.get('statistics', {})
                    channel_branding = channel_data.get('brandingSettings', {})
                    # Construct the dictionary for comprehensive channel information
                    channel_detail_info = {
                        'channel_id': channel_id,
                        'channel_name': channel_snippet.get('title', 'N/A'),
                        'channel_description': channel_snippet.get('description', ''),
                        'channel_custom_url': channel_snippet.get('customUrl', 'N/A'),
                        'channel_published_at': channel_snippet.get('publishedAt', 'N/A'),
                        'channel_country': channel_snippet.get('country', 'N/A'),
                        'channel_default_language': channel_branding.get('channel', {}).get('defaultLanguage', 'N/A'),
                        'channel_keywords': channel_branding.get('channel', {}).get('keywords', 'N/A'),
                        'channel_subscriber_count': int(channel_stats.get('subscriberCount', 0)),
                        'channel_video_count': int(channel_stats.get('videoCount', 0)),
                        'channel_view_count': int(channel_stats.get('viewCount', 0)),
                        'channel_hidden_subscriber_count': channel_stats.get('hiddenSubscriberCount', False),
                    }
                    # Use ChannelScraper to extract email and links from About page
                    # Prefer @username format over channel ID for better scraping
                    if channel_detail_info['channel_custom_url'] and channel_detail_info['channel_custom_url'] != 'N/A':
                        # Use the @username format (e.g., @MrBeast)
                        channel_url = f"https://www.youtube.com/{channel_detail_info['channel_custom_url']}"
                     
                    else:
                        # Fallback to channel ID format if no custom URL available
                        channel_url = f"https://www.youtube.com/channel/{channel_id}"
                      
                    channel_detail_info['channel_url'] = channel_url
                   
                    # Run the scraper in an executor to avoid blocking the async event loop
                    # scrape_result = await loop.run_in_executor(None, scraper.extract_from_channel, channel_url)
                    # print(json.dumps(scrape_result, indent=2))
                    
                    # channel_detail_info['email'] = scrape_result['email']
                    # channel_detail_info['links'] = scrape_result['links']
                    # print(json.dumps({'channel_id': channel_id, 'email': scrape_result['email'], 'links': scrape_result['links']}, indent=2))
                    channels_info.append(channel_detail_info)
                    fetched += 1
                    if fetched >= limit:
                        break

                next_page_token = search_response.get('nextPageToken')
                if not next_page_token:
                    break  # No more pages
            
            # Clean up the scraper
            # if 'scraper' in locals():
            #     scraper.close()
            
            return channels_info

        except HttpError as e:
            print(f"YouTube API error: {str(e)}")
            raise Exception(f"YouTube API error: {str(e)}")
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            raise Exception(f"Unexpected error: {str(e)}")

    async def get_last_videos_for_channel(self, channel_id: str, n: int = 3) -> list:
        """
        Fetch the last n videos for a channel using the uploads playlist.
        Returns a list of dicts with title, description, and view count for each video.
        """
        loop = asyncio.get_event_loop()
        # Get the uploads playlist ID
        channel_response = await loop.run_in_executor(
            None,
            partial(
                self.youtube.channels().list,
                part='contentDetails',
                id=channel_id
            )
        )
        channel_response = await loop.run_in_executor(None, channel_response.execute)
        items = channel_response.get('items', [])
        if not items:
            return []
        uploads_playlist_id = items[0]['contentDetails']['relatedPlaylists']['uploads']
        # Get the last n videos from the uploads playlist
        playlist_items_request = self.youtube.playlistItems().list(
            part='snippet',
            playlistId=uploads_playlist_id,
            maxResults=n
        )
        playlist_items_response = await loop.run_in_executor(None, playlist_items_request.execute)
        video_ids = [item['snippet']['resourceId']['videoId'] for item in playlist_items_response.get('items', [])]
        if not video_ids:
            return []
        # Fetch video details for these video IDs
        videos_request = self.youtube.videos().list(
            part='snippet,statistics',
            id=','.join(video_ids)
        )
        videos_response = await loop.run_in_executor(None, videos_request.execute)
        results = []
        for item in videos_response.get('items', []):
            snippet = item.get('snippet', {})
            stats = item.get('statistics', {})
            results.append({
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'view_count': int(stats.get('viewCount', 0))
            })
        return results

    async def extract_emails_and_links_from_urls(self, video_url_items: List[dict]) -> List[dict]:
        """
        Given a list of dicts with 'id' and 'url', extract emails and links from each using ChannelScraper.
        Returns a list of dicts: { 'id': ..., 'url': ..., 'email': ..., 'links': ... }
        """
        loop = asyncio.get_event_loop()
        scraper = ChannelScraper()
        results = []
        try:
            for item in video_url_items:
                url = item['url']
                vid = item['id']
                # Run the scraper in an executor to avoid blocking the async event loop
                scrape_result = await loop.run_in_executor(None, scraper.extract_from_channel, url)
             
                results.append({
                    'id': vid,
                    'url': url,
                    'email': scrape_result.get('email'),
                    'links': scrape_result.get('links'),
                })
        finally:
            scraper.close()
        return results

