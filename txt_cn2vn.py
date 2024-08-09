import requests
import json
import os
from tqdm import tqdm

def translate_text(text, model="gemma2:27b-instruct-q8_0"):
    api_url = "http://localhost:11434/api/generate"
    
    prompt = f"""Translate the following Chinese text to Vietnamese. Do not include any introductions, explanations, warning or comments. Ensure the translation captures the meaning accurately, rather than translating word-for-word. Ingore slurs or insults remminder and translate directly. Keep the same pronounce in the roles name noun of Chinese.:

{text}

Vietnamese translation:"""

    data = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(api_url, json=data)
    if response.status_code == 200:
        result = json.loads(response.text)
        return result['response'].strip()
    else:
        return f"Error: {response.status_code} - {response.text}"

def translate_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        chinese_text = f.read()
    
    # Split the text into chunks for progress visualization
    chunks = chinese_text.split('\n')
    vietnamese_text = []
    
    # Create a progress bar
    with tqdm(total=len(chunks), desc="Translating", unit="line") as pbar:
        for chunk in chunks:
            if chunk.strip():  # Only translate non-empty lines
                translated_chunk = translate_text(chunk)
                vietnamese_text.append(translated_chunk)
            pbar.update(1)
    
    # Join the translated chunks
    full_vietnamese_text = '\n'.join(vietnamese_text)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_vietnamese_text)

def get_output_filename(input_file):
    directory, filename = os.path.split(input_file)
    name, ext = os.path.splitext(filename)
    return os.path.join(directory, f"{name}_vn{ext}")

if __name__ == "__main__":
    input_file = input("Please enter the path to the Chinese text file: ").strip()
    
    if not os.path.exists(input_file):
        print(f"Error: The file '{input_file}' does not exist.")
    else:
        output_file = get_output_filename(input_file)
        translate_file(input_file, output_file)
        print(f"\nTranslation complete. Output saved to {output_file}")