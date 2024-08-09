import os
import re
import html
from google.cloud import translate_v2 as translate
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, TimeoutError
from tqdm import tqdm

def get_translate_client():
    translate_client = translate.Client()
    return translate_client

def translate_text(translate_client, text, target_language):
    result = translate_client.translate(text, target_language=target_language)
    translated_text = result['translatedText']
    return html.unescape(translated_text)

def srt_to_vtt(srt_content):
    vtt_content = "WEBVTT\n\n"
    vtt_content += srt_content.replace(',', '.')
    return vtt_content

def translate_srt_file_to_vtt(translate_client, file_path, target_language):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    srt_blocks = re.split(r'(\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n)', content)
    translated_blocks = []

    for i in range(1, len(srt_blocks), 2):
        translated_text = translate_text(translate_client, srt_blocks[i + 1], target_language)
        translated_blocks.append(srt_blocks[i] + translated_text + '\n')
    
    translated_srt_content = ''.join(translated_blocks)
    return srt_to_vtt(translated_srt_content)

def process_file(translate_client, file_path):
    base_name, ext = os.path.splitext(file_path)
    if ext.lower() != '.mp4':
        return None
    
    srt_file = base_name + '.srt'
    en_vtt_file = base_name + '_en.vtt'
    vn_vtt_file = base_name + '_vn.vtt'

    if os.path.exists(en_vtt_file) and os.path.exists(vn_vtt_file):
        return f"Skipping {file_path}: EN and VN translation files already exist."

    if os.path.exists(srt_file):
        if not os.path.exists(en_vtt_file):
            translated_content_en = translate_srt_file_to_vtt(translate_client, srt_file, 'en')
            with open(en_vtt_file, 'w', encoding='utf-8') as file:
                file.write(translated_content_en)
        
        if not os.path.exists(vn_vtt_file):
            translated_content_vn = translate_srt_file_to_vtt(translate_client, srt_file, 'vi')
            with open(vn_vtt_file, 'w', encoding='utf-8') as file:
                file.write(translated_content_vn)
        
        return f"Translated {file_path} to English and Vietnamese."
    else:
        return f"SRT file for {file_path} not found. Skipping translation."

def main():
    folder_path = os.getcwd()
    translate_client = get_translate_client()

    mp4_files = []
    for root, _, files in os.walk(folder_path):
        for file_name in files:
            if file_name.endswith('.mp4'):
                mp4_files.append(os.path.join(root, file_name))

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(process_file, translate_client, file_path): file_path for file_path in mp4_files}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Translating files"):
            try:
                result = future.result(timeout=60)
                if result:
                    print(result)
            except TimeoutError:
                print(f"Timeout: Skipping {futures[future]} due to taking longer than 60 seconds.")

if __name__ == '__main__':
    main()