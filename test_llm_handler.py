import asyncio
import os
from dotenv import load_dotenv
from app.services.llm_handler import LLMHandler

load_dotenv()

async def test_llm_handler():
    """Test the LLM handler's extract_contact_info method"""
    try:
        llm = LLMHandler()
        
        # Test data - a sample channel that should be ICP
        test_description = "Welcome to our educational channel! We create in-depth documentaries about history, science, and technology. Our videos feature high-quality 3D animations and visualizations to bring complex topics to life. Contact us at contact@example.com for collaborations."
        
        test_channel_details = {
            'channel_name': 'Educational History Channel',
            'sub_count': '500000',
            'about': 'We create educational content about history and science with 3D animations',
            'links': ['https://patreon.com/example', 'https://instagram.com/example'],
            'last_3_titles': [
                'How Rome Was Built: A 3D Journey Through Ancient Architecture',
                'The Science Behind Black Holes: Visualizing the Unseen',
                'World War II: The Battle of Normandy in 3D'
            ],
            'avg_views': '300000',
            'last_3_descriptions': [
                'Explore ancient Rome through stunning 3D reconstructions...',
                'Journey into the mysterious world of black holes...',
                'Experience the D-Day invasion like never before...'
            ],
            'country': 'United States'
        }
        
        print("Testing LLM Handler...")
        print("=" * 50)
        
        result = await llm.extract_contact_info(test_description, test_channel_details)
        
        print("LLM Response:")
        print(f"Email: {result.get('email', 'Not found')}")
        print(f"Contact Links: {result.get('contact_links', [])}")
        print(f"Is ICP: {result.get('isicp', 'Not found')}")
        print(f"Why: {result.get('why', 'Not found')}")
        print(f"High Ticket: {result.get('high_ticket', 'Not found')}")
        print(f"Potential ICP: {result.get('potential_icp', 'Not found')}")
        
        # Check if isicp is present
        if 'isicp' in result:
            print("\n✅ SUCCESS: isicp field is present in response")
        else:
            print("\n❌ ERROR: isicp field is missing from response")
            
        return result
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None

if __name__ == "__main__":
    asyncio.run(test_llm_handler()) 