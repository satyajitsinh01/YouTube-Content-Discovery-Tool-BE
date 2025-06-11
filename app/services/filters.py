from typing import List, Dict, Any

class VideoFilter:
    def __init__(self, min_views: int = 100000, min_subscribers: int = 100000, allowed_countries: List[str] = None):
        self.min_views = min_views
        self.min_subscribers = min_subscribers
        self.allowed_countries = allowed_countries or ['US', 'GB', 'IN']  # USA, UK, India

    def filter_videos(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter videos based on view count, subscriber count, and country criteria.
        """
        filtered_videos = []
        print("videos============", self.min_views, self.min_subscribers, self.allowed_countries)
        
        for video in videos:
            # Check view count
            if video['view_count'] < self.min_views:
                continue
                
            # Check subscriber count
            if video['subscriber_count'] < self.min_subscribers:
                continue
                
            # Check country if available
            country = video.get('country')
            if country and country not in self.allowed_countries:
                continue
                
            filtered_videos.append(video)
            
        return filtered_videos 