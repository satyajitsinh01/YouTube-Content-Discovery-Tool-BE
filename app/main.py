from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.services.filters import VideoFilter
from app.services.youtube_search import YouTubeSearch
from app.services.llm_handler import LLMHandler
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Check if environment variables are set
youtube_key = os.getenv("YOUTUBE_API_KEY")

if not youtube_key or youtube_key == "your_youtube_api_key_here":
    raise ValueError("YOUTUBE_API_KEY is not set in .env file")

app = FastAPI(
    title="YouTube Content Discovery Tool",
    description="A tool that uses LLM for synonym expansion and YouTube API for content discovery",
    version="1.0.0"
)

class SearchQuery(BaseModel):
    query: str
    min_subscribers: Optional[int] = None
    min_views: Optional[int] = None
    country_code: Optional[str] = None
    limit: Optional[int] = None

class VideoResult(BaseModel):
    title: str
    link: str
    channel_name: str
    subscriber_count: int
    view_count: int
    country: Optional[str] = None
    email: Optional[str] = None
    contact_links: Optional[List[str]] = None
    
    # Additional video details
    description: Optional[str] = None
    published_at: Optional[str] = None
    tags: Optional[List[str]] = None
    category_id: Optional[str] = None
    duration: Optional[str] = None
    definition: Optional[str] = None
    caption_available: Optional[str] = None
    licensed_content: Optional[bool] = None
    projection: Optional[str] = None
    topic_categories: Optional[List[str]] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    
    # Additional channel details
    channel_info: Optional[dict] = None

class SearchResponse(BaseModel):
    results: List[VideoResult]
    related_keywords: List[str]
    
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=False,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.post("/search", response_model=SearchResponse)
async def search_videos(search_query: SearchQuery):
    """
    Search for videos based on the query and filter criteria.
    Returns a list of VideoResult objects and related keywords.
    """
    print("search_query============", search_query)

    try:
        # Initialize services
        llm_service = LLMHandler()
        youtube_service = YouTubeSearch()
        
        # Initialize filter service with dynamic parameters
        filter_service = VideoFilter(
            min_views=search_query.min_views or 100000,  # Use default if not provided
            min_subscribers=search_query.min_subscribers or 100000,  # Use default if not provided
            allowed_countries=search_query.country_code.replace(" ", "").split(",") if search_query.country_code else None
        )

        # Get related keywords using LLM
        related_keywords = await llm_service.generate_synonyms(search_query.query)

        # Search videos for each keyword
        all_videos = []
        for keyword in related_keywords:
            videos = await youtube_service.search_videos(keyword)
            filtered_videos = await filter_service.filter_videos(videos)
            all_videos.extend(filtered_videos)

        # Apply limit if specified
        if search_query.limit:
            all_videos = all_videos[:search_query.limit]
        
        # Debug: Ensure all required fields are present
        for i, video in enumerate(all_videos):
            # Ensure all required fields are present with valid values
            # if 'link' not in video or not video['link']:
            #     print(f"WARNING: Video {i} is missing 'link' field. Adding default value.")
            #     video['link'] = f"https://youtube.com/watch?v=missing-{i}"
            
            if 'title' not in video or not video['title']:
                video['title'] = f"Video {i}"
                
            if 'channel_name' not in video or not video['channel_name']:
                video['channel_name'] = "Unknown Channel"
                
            if 'subscriber_count' not in video:
                video['subscriber_count'] = 0
                
            if 'view_count' not in video:
                video['view_count'] = 0
            
            # Print the keys for the first video to debug
            if i == 0:
                print(f"First video keys: {video.keys()}")
                print(f"First video link: {video.get('link', 'MISSING')}")
                
        # Convert the list to a proper SearchResponse
        try:
            response = SearchResponse(
                results=all_videos,
                related_keywords=related_keywords
            )
            return response
        except Exception as e:
            print(f"Error creating SearchResponse: {str(e)}")
            # If there's an error, try to fix the data and return a valid response
            fixed_videos = []
            for video in all_videos:
                try:
                    # Create a minimal valid video
                    fixed_video = {
                        'title': video.get('title', 'Unknown Title'),
                        # 'link': video.get('link', 'https://youtube.com'),
                        'channel_name': video.get('channel_name', 'Unknown Channel'),
                        'subscriber_count': int(video.get('subscriber_count', 0)),
                        'view_count': int(video.get('view_count', 0)),
                    }
                    fixed_videos.append(fixed_video)
                except Exception:
                    continue
            
            return SearchResponse(
                results=fixed_videos if fixed_videos else [
                    {
                        'title': 'Error processing results',
                        # 'link': 'https://youtube.com',
                        'channel_name': 'Error',
                        'subscriber_count': 0,
                        'view_count': 0
                    }
                ],
                related_keywords=related_keywords
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "YouTube Content Discovery Tool API"}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8002) 

   
if __name__ == "__main__":
    import uvicorn
    import os

    # port = int(os.environ.get("PORT", 8000))  # default to 8000 locally
    port = int(os.getenv("PORT", 3000))

    uvicorn.run(app, host="0.0.0.0", port=port)
