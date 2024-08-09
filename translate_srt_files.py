import os
import re
import html
from google.cloud import translate_v2 as translate

def get_translate_client():
    translate_client = translate.Client()
    return translate_client

def translate_text(translate_client, text, target_language):
    result = translate_client.translate(text, target_language=target_language)
    translated_text = result['translatedText']
    return html.unescape(translated_text)

def translate_srt_file(translate_client, file_path, target_language):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    srt_blocks = re.split(r'(\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n)', content)
    translated_blocks = []

    for i in range(1, len(srt_blocks), 2):
        translated_text = translate_text(translate_client, srt_blocks[i + 1], target_language)
        translated_blocks.append(srt_blocks[i] + translated_text + '\n')
    
    return ''.join(translated_blocks)

def main():
    # Ensure GOOGLE_APPLICATION_CREDENTIALS environment variable is set
    folder_path = '/Users/hendrywang/Downloads/MyUncle'  # Replace with your folder path

    translate_client = get_translate_client()

    for file_name in os.listdir(folder_path):
        if file_name.endswith('.srt'):
            base_name = os.path.splitext(file_name)[0]
            file_path = os.path.join(folder_path, file_name)
            
            translated_content_en = translate_srt_file(translate_client, file_path, 'en')
            translated_file_path_en = os.path.join(folder_path, base_name + '_en.srt')
            with open(translated_file_path_en, 'w', encoding='utf-8') as file:
                file.write(translated_content_en)
            
            translated_content_vn = translate_srt_file(translate_client, file_path, 'vi')
            translated_file_path_vn = os.path.join(folder_path, base_name + '_vn.srt')
            with open(translated_file_path_vn, 'w', encoding='utf-8') as file:
                file.write(translated_content_vn)
            
            print(f'Translated {file_name} to English and Vietnamese.')

if __name__ == '__main__':
    main()