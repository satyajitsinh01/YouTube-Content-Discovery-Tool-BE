from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from app.services.filters import VideoFilter
from app.services.youtube_search import YouTubeSearch
from app.services.llm_handler import LLMHandler
from typing import List, Optional, Dict
import os
from dotenv import load_dotenv
import re
from app.services.channel_scraper import ChannelScraper
from fastapi.responses import JSONResponse
from fastapi.requests import Request

load_dotenv()

# Check if environment variables are set
youtube_key = os.getenv("YOUTUBE_API_KEY")
CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY")
PROXY = os.getenv("PROXY")

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
    isicp: Optional[bool] = None
    # Additional channel details
    channel_info: Optional[dict] = None

class SearchResponse(BaseModel):
    results: List[VideoResult]
    related_keywords: List[str]

class VideoUrlItem(BaseModel):
    id: str
    url: str

class ExtractEmailRequest(BaseModel):
    video_urls: List[VideoUrlItem]

class EmailResult(BaseModel):
    video_url: VideoUrlItem
    email: Optional[str] = None
    error: Optional[str] = None
    links: List[str]
    
class ChannelDiscoveryResult(BaseModel):
    id: str
    channel_name: str
    subscriber_count: int
    country: str
    about: str
    links: List[str]
    emails: List[str]
    last_3_videos: List[dict]
    average_views: float
    channel_url: str
    is_icp: Optional[bool] = None

class ChannelDiscoveryResponse(BaseModel):
    results: List[ChannelDiscoveryResult]
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

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled error: {exc}")  # Log for debugging
    return JSONResponse(
        status_code=500,
        content={"detail": "Oops! Something went wrong. Please try again later."}
    )

@app.post("/search", response_model=ChannelDiscoveryResponse)
async def search_videos(search_query: SearchQuery):
    """
    Search for channels based on the query and filter criteria.
    Returns a list of ChannelDiscoveryResult objects and related keywords.
    """
    print("search_query============", search_query)

    try:
        llm_service = LLMHandler()
        youtube_service = YouTubeSearch()
        print(f"DEBUG: Received country_code: '{search_query.country_code}'")
        allowed_countries = search_query.country_code.replace(" ", "").split(",") if search_query.country_code and search_query.country_code.strip() else None
        print(f"DEBUG: Processed allowed_countries: {allowed_countries}")
        filter_service = VideoFilter(
            min_views=search_query.min_views or 100000,
            min_subscribers=search_query.min_subscribers or 100000,
            allowed_countries=allowed_countries
        )
        related_keywords = await llm_service.generate_synonyms(search_query.query)
        all_channels = []
        seen_channel_ids = set()
        total_channels_visited = 0
        for keyword in related_keywords:
            channels = await youtube_service.search_videos(keyword, limit=search_query.limit or 5)
            for channel in channels:
                total_channels_visited += 1
                channel_id = channel.get('channel_id')
                if not channel_id or channel_id in seen_channel_ids:
                    continue
                seen_channel_ids.add(channel_id)
                if allowed_countries and channel.get('channel_country') not in allowed_countries:
                    continue
                if channel.get('channel_subscriber_count', 0) < (search_query.min_subscribers or 100000):
                    continue
                about = channel.get('channel_description', '')
                # Extract all links from about
                url_pattern = r'https?://[^\s<>"\)\(]+'
                links = channel.get('links', [])
                # Extract all emails from about
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, about)
                # Get last 3 videos
                last_videos = await youtube_service.get_last_videos_for_channel(channel_id, n=3)
                last_3_videos = [{
                    'title': v['title'],
                    'description': v['description'],
                    'view_count': v['view_count']
                } for v in last_videos]
                average_views = float(sum(v['view_count'] for v in last_videos)) / len(last_videos) if last_videos else 0.0
                
                # Use LLM to analyze channel and extract contact info
                channel_details = {
                    'channel_name': channel.get('channel_name', ''),
                    'sub_count': channel.get('channel_subscriber_count', 0),
                    'about': about,
                    'links': links,
                    'last_3_titles': [v['title'] for v in last_3_videos],
                    'avg_views': average_views,
                    'last_3_descriptions': [v['description'] for v in last_3_videos],
                    'country': channel.get('channel_country', '')
                }
                
                llm_analysis = await llm_service.extract_contact_info(about, channel_details)
                
                # Use LLM extracted emails and contact links if available
                llm_emails = llm_analysis.get('email', '')
                if llm_emails:
                    emails = [llm_emails] if llm_emails not in emails else emails
                
                llm_contact_links = llm_analysis.get('contact_links', [])
                if llm_contact_links:
                    links.extend(llm_contact_links)
                
                all_channels.append(ChannelDiscoveryResult(
                    id=channel_id,
                    channel_name=channel.get('channel_name', ''),
                    subscriber_count=channel.get('channel_subscriber_count', 0),
                    country=channel.get('channel_country', ''),
                    about=about,
                    links=links,
                    emails=emails,
                    channel_url=channel.get('channel_url', ''),
                    last_3_videos=last_3_videos,
                    average_views=average_views,
                    is_icp=llm_analysis.get('isicp', False)
                ))
                if search_query.limit and len(all_channels) >= search_query.limit:
                    break
            if search_query.limit and len(all_channels) >= search_query.limit:
                break
        print(f"Total channels visited: {total_channels_visited}")
        return ChannelDiscoveryResponse(results=all_channels, related_keywords=related_keywords)
    except Exception as e:
        # Log the real error for debugging
        print(f"Internal error: {e}")
        raise HTTPException(
            status_code=500,
            detail="something went wrong on our end. Please try again later or contact support if the issue persists."
        )

@app.post("/extract-emails", response_model=List[EmailResult])
async def extract_emails(req: ExtractEmailRequest):
    youtube_service = YouTubeSearch()
    try:
        # Convert HttpUrl to str for the service method
        # url_list = [str(url) for url in req.video_urls]
        # Now req.video_urls is a list of VideoUrlItem
        results = await youtube_service.extract_emails_and_links_from_urls([
            {"id": v.id, "url": v.url} for v in req.video_urls
        ])
        email_results = []
        for result in results:
            email_results.append(
                EmailResult(
                    video_url=VideoUrlItem(id=result.get('id'), url=result.get('url')),
                    email=result.get('email'),
                    links=result.get('links') or [],
                    error=None if result.get('email') else 'No email found'
                )
            )
        return email_results
    except Exception as e:
        # If the whole batch fails, return a single error result for each input
        return [
            EmailResult(
                video_url=VideoUrlItem(id=v.id, url=v.url),
                email=None,
                links=[],
                error=str(e)
            ) for v in req.video_urls
        ]

@app.get("/")
async def root():
    return {"message": "YouTube Content Discovery Tool API"}

   
if __name__ == "__main__":
    import uvicorn
    import os

    # port = int(os.environ.get("PORT", 8000))  # default to 8000 locally
    port = int(os.getenv("PORT", 8000))

    uvicorn.run(app, host="0.0.0.0", port=port)
