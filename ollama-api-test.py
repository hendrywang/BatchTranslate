import aiohttp
import asyncio

async def test_ollama_api():
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "gemma2",
        "prompt": "Translate the following Chinese text to English: 你好，世界！",
        "stream": False
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    print("API Response:", result['response'].strip())
                    print("API is working correctly!")
                else:
                    print(f"API returned status code: {response.status}")
                    print("Response content:", await response.text())
    except aiohttp.ClientError as e:
        print(f"Error connecting to the API: {e}")
    except asyncio.TimeoutError:
        print("Request timed out. The API might be slow or unresponsive.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(test_ollama_api())
