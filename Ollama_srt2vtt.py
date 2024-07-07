import os
import asyncio
import aiohttp
import aiofiles
from tqdm import tqdm
import time
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MAX_RETRIES = 3
TIMEOUT = 60  # 1 minute
MAX_CONCURRENT_FILES = 5  # Number of files to process in parallel
MAX_CONCURRENT_REQUESTS = 10  # Number of concurrent API requests
RATE_LIMIT = 10  # requests per second

class RateLimiter:
    def __init__(self, rate_limit):
        self.rate_limit = rate_limit
        self.tokens = rate_limit
        self.last_refill = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            while self.tokens < 1:
                self._refill()
                await asyncio.sleep(0.1)
            self.tokens -= 1

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.rate_limit
        self.tokens = min(self.rate_limit, self.tokens + new_tokens)
        self.last_refill = now

async def translate_text(session, text, target_language, rate_limiter, retries=0):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "gemma2",
        "prompt": f"Translate the following Chinese text to {target_language}. Provide only the direct translation without any explanations or additional text:\n\n{text}",
        "stream": False
    }
    
    await rate_limiter.acquire()
    try:
        async with session.post(url, json=payload, timeout=TIMEOUT) as response:
            result = await response.json()
            return result['response'].strip()
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        if retries < MAX_RETRIES:
            await asyncio.sleep(2 ** retries)  # Exponential backoff
            return await translate_text(session, text, target_language, rate_limiter, retries + 1)
        else:
            logging.error(f"Failed to translate after {MAX_RETRIES} retries: {text[:50]}...")
            return f"TRANSLATION_FAILED: {text}"

def format_time(time_str):
    # Convert SRT time format to VTT format
    return re.sub(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})', r'\1:\2:\3.\4', time_str)

async def process_srt_file(session, file_path, target_languages, rate_limiter, semaphore):
    async with semaphore:
        base_name = os.path.splitext(file_path)[0]
        
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        lines = content.strip().split('\n')
        translated_contents = {lang: [] for lang in target_languages}
        
        tasks = []
        for i in range(0, len(lines), 4):
            block = lines[i:i+4]
            if len(block) < 3:
                continue
            
            index, timing, text = block[:3]
            formatted_timing = ' --> '.join(map(format_time, timing.split(' --> ')))
            
            for lang in target_languages:
                task = asyncio.create_task(translate_text(session, text, lang, rate_limiter))
                tasks.append((index, formatted_timing, lang, task))
        
        for index, timing, lang, task in tasks:
            translation = await task
            translated_contents[lang].extend([index, timing, translation, ''])
        
        for lang, content in translated_contents.items():
            output_file = f"{base_name}_{lang}.vtt"
            async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
                await f.write("WEBVTT\n\n")
                await f.write('\n'.join(content))
        
        logging.info(f"Processed file: {file_path}")

async def process_files(files):
    target_languages = ['en', 'vi']
    timeout = aiohttp.ClientTimeout(total=TIMEOUT)
    rate_limiter = RateLimiter(RATE_LIMIT)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_FILES)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = [process_srt_file(session, file, target_languages, rate_limiter, semaphore) for file in files]
        for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Processing files"):
            await task

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