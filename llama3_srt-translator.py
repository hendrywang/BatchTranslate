import os
import asyncio
import aiohttp
import aiofiles
from tqdm import tqdm
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MAX_RETRIES = 3
TIMEOUT = 60  # 1 minute
RATE_LIMIT = 1  # requests per second

async def translate_text(session, text, target_language, retries=0):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3",
        "prompt": f"Translate the following Chinese text to {target_language}: {text}",
        "stream": False
    }
    
    try:
        async with session.post(url, json=payload, timeout=TIMEOUT) as response:
            result = await response.json()
            return result['response'].strip()
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        if retries < MAX_RETRIES:
            await asyncio.sleep(2 ** retries)  # Exponential backoff
            return await translate_text(session, text, target_language, retries + 1)
        else:
            logging.error(f"Failed to translate after {MAX_RETRIES} retries: {text[:50]}...")
            return f"TRANSLATION_FAILED: {text}"

async def process_srt_file(session, file_path, target_languages):
    base_name = os.path.splitext(file_path)[0]
    
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
        content = await f.read()
    
    lines = content.strip().split('\n')
    translated_contents = {lang: [] for lang in target_languages}
    
    for i in range(0, len(lines), 4):
        block = lines[i:i+4]
        if len(block) < 3:
            continue
        
        index, timing, text = block[:3]
        
        for lang in target_languages:
            translation = await translate_text(session, text, lang)
            translated_contents[lang].extend([index, timing, translation, ''])
        
        await asyncio.sleep(1 / RATE_LIMIT)  # Simple rate limiting
    
    for lang, content in translated_contents.items():
        output_file = f"{base_name}_{lang}.vtt"
        async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
            await f.write("WEBVTT\n\n")
            await f.write('\n'.join(content))
    
    logging.info(f"Processed file: {file_path}")

async def process_files(files):
    target_languages = ['en', 'vi']
    timeout = aiohttp.ClientTimeout(total=TIMEOUT)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for file in tqdm(files, desc="Processing files"):
            try:
                await process_srt_file(session, file, target_languages)
            except Exception as e:
                logging.error(f"Error processing file {file}: {e}")

def find_srt_files(directory):
    srt_files = []
    mp4_files = []
    for file in os.listdir(directory):
        if file.endswith('.srt'):
            srt_files.append(os.path.join(directory, file))
        elif file.endswith('.mp4'):
            mp4_files.append(file)
    
    missing_srt = [mp4 for mp4 in mp4_files if mp4[:-4] + '.srt' not in [os.path.basename(f) for f in srt_files]]
    return srt_files, missing_srt

async def main():
    current_dir = os.getcwd()
    srt_files, missing_srt = find_srt_files(current_dir)
    
    if missing_srt:
        logging.warning("The following MP4 files are missing corresponding SRT files:")
        for file in missing_srt:
            logging.warning(f"- {file}")
    
    if not srt_files:
        logging.warning("No SRT files found in the current directory.")
        return
    
    logging.info(f"Found {len(srt_files)} SRT files to process.")
    
    start_time = time.time()
    await process_files(srt_files)
    end_time = time.time()
    
    logging.info(f"Translation completed. VTT files have been created.")
    logging.info(f"Total processing time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())