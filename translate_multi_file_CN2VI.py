import os
import re
import requests
import json
from tqdm import tqdm
import concurrent.futures

def translate_text_with_context(text_lines, prev_lines, next_lines, target_language="Vietnamese"):
    url = "http://localhost:11434/api/generate"
    context = f"Previous lines: {' '.join(prev_lines)}\nCurrent lines: {' '.join(text_lines)}\nNext lines: {' '.join(next_lines)}"
    prompt = f"""Translate the following Chinese movie subtitle to {target_language}.

    Instructions:
    1. Understand the natural meaning and nuance of the Chinese text in the context of the movie.
    2. Express this meaning naturally in {target_language}, as if originally written in {target_language}.
    3. Keep the original phrase.
    4. Do not include any introductions, explanations, warning or comments.
    5. Ensure the translation captures the meaning accurately, rather than translating word-for-word.
    6. Directly translate the slurs or insults words. Use same pronunciation in Chinese of character name and noun..
    7. Maintain the style appropriate for movie subtitles (concise yet clear).

    Context:
    {context}
    
    Translate only the current lines, preserving the line structure:"""
    
    data = {
        "model": "gemma2:27b-instruct-q8_0",
        "prompt": prompt,
        "stream": False
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        try:
            result = response.json()
            translation = result.get('response', '')
            translated_lines = translation.strip().split('\n')
            # Ensure we have the same number of lines as the original
            while len(translated_lines) < len(text_lines):
                translated_lines.append('')
            return translated_lines[:len(text_lines)]
        except json.JSONDecodeError:
            print(f"Error decoding JSON: {response.text}")
            return None
    else:
        print(f"Error: {response.status_code}")
        return None

def srt_to_vtt(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile:
        lines = infile.readlines()

    total_lines = len(lines)
    translated_count = 0

    with open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.write("WEBVTT\n\n")
        
        pbar = tqdm(total=total_lines, desc="Translating", unit="line")
        
        subtitle_blocks = []
        current_block = []
        for line in lines:
            line = line.strip()
            if re.match(r'^\d+$', line):
                if current_block:
                    subtitle_blocks.append(current_block)
                    current_block = []
            current_block.append(line)
        if current_block:
            subtitle_blocks.append(current_block)

        for i, block in enumerate(subtitle_blocks):
            pbar.update(len(block))
            
            outfile.write(f"{block[0]}\n")  # Subtitle number
            outfile.write(f"{block[1].replace(',', '.')}\n")  # Timestamp
            
            text_lines = block[2:]
            prev_lines = subtitle_blocks[i-1][2:] if i > 0 else []
            next_lines = subtitle_blocks[i+1][2:] if i < len(subtitle_blocks) - 1 else []
            
            translated_lines = translate_text_with_context(text_lines, prev_lines, next_lines)
            if translated_lines:
                for line in translated_lines:
                    outfile.write(f"{line}\n")
                translated_count += len(text_lines)
            else:
                for line in text_lines:
                    outfile.write(f"{line}\n")
                print(f"Warning: Could not translate lines: {' '.join(text_lines)}")
            
            outfile.write("\n")
        
        pbar.close()
    
    print(f"Translation complete. Translated {translated_count} lines.")

def file_already_translated(input_file, output_file):
    if not os.path.exists(output_file):
        return False
    return os.path.getmtime(output_file) > os.path.getmtime(input_file)

def process_file(file_info):
    input_path, output_path = file_info
    if file_already_translated(input_path, output_path):
        return f"Skipped: {os.path.basename(input_path)} (already translated)"
    
    srt_to_vtt(input_path, output_path)
    return f"Processed: {os.path.basename(input_path)}"

def process_directory(input_dir, max_workers=5):
    srt_files = [f for f in os.listdir(input_dir) if f.endswith('.srt')]
    srt_files.sort(key=lambda f: int(re.search(r'\d+', f).group()) if re.search(r'\d+', f) else float('inf'))
    
    file_pairs = []
    for srt_file in srt_files:
        input_path = os.path.join(input_dir, srt_file)
        name, _ = os.path.splitext(srt_file)
        output_path = os.path.join(input_dir, f"{name}_vi.vtt")
        file_pairs.append((input_path, output_path))
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(tqdm(executor.map(process_file, file_pairs), total=len(file_pairs), desc="Processing files"))
    
    for result in results:
        print(result)

def process_folders(root_dir, max_workers=5):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        srt_files = [f for f in filenames if f.endswith('.srt')]
        if srt_files:
            print(f"\nProcessing folder: {dirpath}")
            print(f"Found {len(srt_files)} SRT files")
            process_directory(dirpath, max_workers)

def main():
    current_dir = os.getcwd()
    print(f"Starting translation process in: {current_dir}")
    
    max_workers = 5  # You can adjust this number based on your system's capabilities
    process_folders(current_dir, max_workers)
    
    print("\nAll translations complete.")

if __name__ == "__main__":
    main()