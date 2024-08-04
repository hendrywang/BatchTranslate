import os
import re
import requests
import json
from tqdm import tqdm
import time

def translate_text_with_interpretation(text, prev_line, next_line, target_language="Vietnamese", retry_count=0):
    url = "http://localhost:11434/api/generate"
    context = f"Previous line: {prev_line}\nCurrent line: {text}\nNext line: {next_line}"
    prompt = f"""As an expert translator, your task is to translate the following Chinese movie subtitle to {target_language} (Vietnamese).

    Context:
    {context}

    Instructions:
    1. Carefully interpret the Chinese text, considering context, cultural nuances, and idiomatic expressions.
    2. Translate the interpreted meaning into {target_language} (Vietnamese), ensuring it sounds natural and appropriate for subtitles.
    3. CRITICAL: Ensure ALL text is translated to {target_language} (Vietnamese). Do not leave any Chinese characters in your translation.
    4. Maintain the tone and style appropriate for movie subtitles.

    Provide ONLY the final {target_language} (Vietnamese) translation, without any explanations or original text. 
    Your response must contain ONLY Vietnamese words and punctuation."""

    data = {
        "model": "mistral-nemo:12b-instruct-2407-q8_0",  # or any other model you have in Ollama
        "prompt": prompt,
        "stream": False
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        try:
            result = response.json()
            translation = result.get('response', '').strip()
            
            # Check if the translation contains Chinese characters
            if re.search(r'[\u4e00-\u9fff]', translation):
                if retry_count < 3:
                    print(f"Retry {retry_count + 1}: Translation contains Chinese characters, retrying...")
                    time.sleep(1)  # Add a small delay before retrying
                    return translate_text_with_interpretation(text, prev_line, next_line, target_language, retry_count + 1)
                else:
                    print(f"Warning: Translation still contains Chinese characters after retries: {translation}")
                    return fallback_translation(text, target_language)
            
            if not translation:
                print("Warning: Translation is empty, using fallback.")
                return fallback_translation(text, target_language)
            
            return translation
        except json.JSONDecodeError:
            print(f"Error decoding JSON: {response.text}")
            return fallback_translation(text, target_language)
    else:
        print(f"Error: {response.status_code}")
        return fallback_translation(text, target_language)

def fallback_translation(text, target_language="Vietnamese"):
    url = "http://localhost:11434/api/generate"
    prompt = f"""Translate the following Chinese text to {target_language} (Vietnamese) literally, word by word if necessary:

    {text}

    Provide ONLY the {target_language} (Vietnamese) translation, no explanations."""

    data = {
        "model": "mistral-nemo:12b-instruct-2407-q8_0",
        "prompt": prompt,
        "stream": False
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        try:
            result = response.json()
            translation = result.get('response', '').strip()
            return translation if translation else text  # Return original text if translation is empty
        except json.JSONDecodeError:
            return text
    else:
        return text

def srt_to_vtt(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile:
        lines = infile.readlines()

    total_lines = len(lines)
    translated_count = 0
    fallback_count = 0

    with open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.write("WEBVTT\n\n")
        
        pbar = tqdm(total=total_lines, desc="Translating", unit="line")
        
        subtitle_text = []
        for i, line in enumerate(lines):
            pbar.update(1)
            line = line.strip()
            
            if re.match(r'^\d+$', line):
                if subtitle_text:
                    prev_line = subtitle_text[-2] if len(subtitle_text) > 1 else ""
                    next_line = lines[i+2].strip() if i+2 < total_lines else ""
                    translated_line = translate_text_with_interpretation(subtitle_text[-1], prev_line, next_line)
                    outfile.write(translated_line + '\n')
                    translated_count += 1
                    if translated_line == subtitle_text[-1]:
                        fallback_count += 1
                    subtitle_text = []
                outfile.write(line + '\n')
            elif '-->' in line:
                outfile.write(line.replace(',', '.') + '\n')
            elif line:
                subtitle_text.append(line)
            else:
                outfile.write('\n')
        
        # Handle the last subtitle
        if subtitle_text:
            prev_line = subtitle_text[-2] if len(subtitle_text) > 1 else ""
            translated_line = translate_text_with_interpretation(subtitle_text[-1], prev_line, "")
            outfile.write(translated_line + '\n')
            translated_count += 1
            if translated_line == subtitle_text[-1]:
                fallback_count += 1
        
        pbar.close()
    
    print(f"Translation complete. Translated {translated_count} lines.")
    print(f"Fallback translation used for {fallback_count} lines.")

def main():
    input_path = input("Enter the path of the original Chinese SRT file: ")
    
    if not os.path.exists(input_path):
        print("Error: File not found.")
        return
    
    directory, filename = os.path.split(input_path)
    name, _ = os.path.splitext(filename)
    output_path = os.path.join(directory, f"{name}_vi.vtt")
    
    print(f"Starting translation of {input_path}")
    print(f"Output will be saved to {output_path}")
    
    srt_to_vtt(input_path, output_path)
    print(f"Translation complete. Output file: {output_path}")

if __name__ == "__main__":
    main()