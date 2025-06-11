import os
import asyncio
import httpx
from openai import AsyncOpenAI
from googleapiclient.discovery import build
from dotenv import load_dotenv

async def test_openai_api():
    print("\nTesting OpenAI API Key...")
    try:
        # Load environment variables
        load_dotenv()
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ Error: OPENAI_API_KEY not found in .env file")
            return False
            
        # Initialize OpenAI client with custom httpx client
        async with httpx.AsyncClient() as http_client:
            client = AsyncOpenAI(
                api_key=api_key,
                http_client=http_client
            )
            
            # Try a simple completion
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Say 'Hello, API test successful!'"}],
                max_tokens=10
            )
            
            print("✅ OpenAI API Key is valid!")
            print(f"Response: {response.choices[0].message.content}")
            return True
        
    except Exception as e:
        print(f"❌ Error with OpenAI API: {str(e)}")
        return False

def test_youtube_api():
    print("\nTesting YouTube API Key...")
    try:
        # Load environment variables
        load_dotenv()
        
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            print("❌ Error: YOUTUBE_API_KEY not found in .env file")
            return False
            
        # Initialize YouTube API client
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        # Try a simple search
        request = youtube.search().list(
            part="snippet",
            q="test",
            maxResults=1
        )
        response = request.execute()
        
        print("✅ YouTube API Key is valid!")
        print(f"Found video: {response['items'][0]['snippet']['title']}")
        return True
        
    except Exception as e:
        print(f"❌ Error with YouTube API: {str(e)}")
        return False

async def main():
    print("API Key Verification Tool")
    print("------------------------")
    
    openai_success = await test_openai_api()
    youtube_success = test_youtube_api()
    
    print("\nSummary:")
    print(f"OpenAI API: {'✅ Working' if openai_success else '❌ Not Working'}")
    print(f"YouTube API: {'✅ Working' if youtube_success else '❌ Not Working'}")
    
    if not openai_success or not youtube_success:
        print("\nTroubleshooting Tips:")
        print("1. Check if your .env file exists in the project root directory")
        print("2. Make sure your .env file has these exact variable names:")
        print("   OPENAI_API_KEY=your_key_here")
        print("   YOUTUBE_API_KEY=your_key_here")
        print("3. Verify that your API keys are correct and not expired")
        print("4. For OpenAI: Check your account has sufficient credits")
        print("5. For YouTube: Ensure the API is enabled in your Google Cloud Console")

if __name__ == "__main__":
    asyncio.run(main()) 