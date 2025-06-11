# YouTube Content Discovery Tool with LLM-Based Synonym Expansion

This tool helps discover YouTube content by using LLM (GPT-4) to generate related search terms and the YouTube Data API to fetch and filter relevant videos.

## Features

- LLM-powered synonym generation for broader content discovery
- YouTube API integration for video search and details
- Advanced filtering based on views, subscribers, and country
- FastAPI backend with async processing
- Structured response with video and channel details

## Prerequisites

- Python 3.11+
- OpenAI API key
- YouTube Data API v3 key

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd youtube-content-discovery
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your API keys:
```
OPENAI_API_KEY=your_openai_api_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here
```

## Running the Application

1. Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

2. The API will be available at `http://localhost:8000`

## API Endpoints

### POST /search
Search for videos with automatic keyword expansion.

Request body:
```json
{
    "query": "your search query"
}
```

Response:
```json
{
    "results": [
        {
            "title": "Video Title",
            "link": "https://youtube.com/watch?v=...",
            "channel_name": "Channel Name",
            "subscriber_count": 1000000,
            "view_count": 500000,
            "country": "US"
        }
    ],
    "related_keywords": [
        "keyword1",
        "keyword2",
        "keyword3",
        "keyword4",
        "keyword5"
    ]
}
```

## API Documentation

Once the server is running, you can access:
- Interactive API documentation at `http://localhost:8000/docs`
- Alternative API documentation at `http://localhost:8000/redoc`

## Error Handling

The API includes comprehensive error handling for:
- Invalid API keys
- YouTube API quota exceeded
- Network issues
- Invalid search queries

## Filtering Criteria

Videos are filtered based on:
- Minimum 100,000 views
- Channel has minimum 100,000 subscribers
- Channel country is India, USA, or UK (if available)

## License

MIT 