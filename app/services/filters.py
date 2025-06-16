from typing import List, Dict, Any

class VideoFilter:
    def __init__(self, min_views: int = 100000, min_subscribers: int = 100000, allowed_countries: List[str] = None):
        self.min_views = min_views
        self.min_subscribers = min_subscribers
        self.allowed_countries = allowed_countries or ['US', 'GB', 'IN']  # USA, UK, India

    def filter_videos(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
                
            # Transform data to match VideoResult model while keeping all additional data
            transformed_video = {
                # Required fields for VideoResult model
                'title': video['video_title'],
                'link': video['video_link'],
                'channel_name': video['channel_name'],
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