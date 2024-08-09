import re
import requests
import os
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from tqdm import tqdm

def srt_to_vtt(input_file, output_file, target_language):
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            content = file.read()

        # Convert SRT to VTT format
        vtt_content = "WEBVTT\n\n" + re.sub(r'(\d{2}:\d{2}:\d{2}),(\d{3})', r'\1.\2', content)

        # Extract and translate only the text parts
        def translate_match(match):
            timing = match.group(1)
            text = match.group(2).strip()
            translated_text = translate_text(text, target_language) if text else ""
            return f"{timing}\n{translated_text}\n"

        translated_content = re.sub(r'(\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3})\n(.*?)(?=\n\d{2}:\d{2}:\d{2}\.\d{3}|$)', translate_match, vtt_content, flags=re.DOTALL)

        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(translated_content)

        return True
    except Exception as e:
        print(f"Error processing {input_file}: {str(e)}")
        return False

def translate_text(text, target_language):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3",
        "prompt": f"Translate the following text from Chinese to {target_language}. Respond with only the translated text, no additional comments: {text}",
        "stream": False
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()['response'].strip()
    except requests.exceptions.RequestException as e:
        print(f"Translation error: {str(e)}")
        return text

def process_srt_file(srt_file):
    base_name = os.path.splitext(srt_file)[0]
    results = []

    for lang, suffix in [("English", "en"), ("Vietnamese", "vn")]:
        output_file = f"{base_name}_{suffix}.vtt"
        success = srt_to_vtt(srt_file, output_file, lang)
        results.append((lang, output_file, success))

    return srt_file, results

def process_srt_files():
    srt_files = glob.glob("*.srt")

    if not srt_files:
        print("No SRT files found in the current directory.")
        return

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=min(os.cpu_count(), len(srt_files))) as executor:
        futures = [executor.submit(process_srt_file, srt_file) for srt_file in srt_files]
        
        with tqdm(total=len(srt_files) * 2, desc="Processing files", unit="translation") as pbar:
            for future in as_completed(futures):
                srt_file, results = future.result()
                for lang, output_file, success in results:
                    if success:
                        pbar.set_postfix_str(f"Translated {srt_file} to {lang}")
                    else:
                        pbar.set_postfix_str(f"Failed to translate {srt_file} to {lang}")
                    pbar.update(1)

    end_time = time.time()
    print(f"\nTotal processing time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    print("Starting SRT to VTT translation process...")
    process_srt_files()
    print("All translations completed.")