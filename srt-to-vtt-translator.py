import re
import requests
import os
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def srt_to_vtt(input_file, output_file, target_language):
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            content = file.read()

        subtitle_blocks = re.split(r'\n\n', content.strip())
        vtt_content = ["WEBVTT\n"]

        for block in subtitle_blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                timing = lines[1].replace(',', '.')
                text = ' '.join(lines[2:])
                translated_text = translate_text(text, target_language)
                vtt_content.append(f"{timing}\n{translated_text}\n")

        with open(output_file, 'w', encoding='utf-8') as file:
            file.write('\n'.join(vtt_content))

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
        print(f"Translating {srt_file} to {lang}...")
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
        future_to_srt = {executor.submit(process_srt_file, srt_file): srt_file for srt_file in srt_files}
        
        for future in as_completed(future_to_srt):
            srt_file = future_to_srt[future]
            try:
                _, results = future.result()
                for lang, output_file, success in results:
                    if success:
                        print(f"{lang} translation saved as {output_file}")
                    else:
                        print(f"Failed to translate {srt_file} to {lang}")
                print(f"Finished processing {srt_file}")
            except Exception as e:
                print(f"Error processing {srt_file}: {str(e)}")

    end_time = time.time()
    print(f"\nTotal processing time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    print("Starting SRT to VTT translation process...")
    process_srt_files()
    print("All translations completed.")