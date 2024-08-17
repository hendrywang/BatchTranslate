# Chinese to Vietnamese Movie Subtitle Translation Scripts

This repository contains a collection of Python scripts designed to assist in translating Chinese movie subtitles to Vietnamese and English. Each script serves a specific purpose in the translation and processing pipeline.

## Table of Contents

1. [translate_file_CN2VI.py](#translate_file_cn2vipy)
2. [poster_maker_root.py](#poster_maker_rootpy)
3. [fasttranslate_root_60s_srt_files_to_vtt.py](#fasttranslate_root_60s_srt_files_to_vttpy)
4. [translate_srt_files.py](#translate_srt_filespy)

## translate_file_CN2VI.py

This script is designed to translate Chinese movie subtitles to Vietnamese using a local language model.

### Key Features:
- Uses a local API endpoint (http://localhost:11434) for translation
- Translates SRT files to VTT format
- Preserves context by considering previous and next lines
- Maintains subtitle timing and structure

### Usage:
1. Ensure the local language model API is running
2. Place SRT files in the script's directory
3. Run the script: `python translate_file_CN2VI.py`

The script will process all SRT files in the current directory and its subdirectories, creating corresponding VTT files with Vietnamese translations.

## poster_maker_root.py

This script generates poster images for movies by extracting frames from video files.

### Key Features:
- Captures frames from video files at specified intervals
- Detects faces in the captured frames
- Selects the best frame based on face detection
- Saves the selected frame as a poster image

### Usage:
1. Place video files (MP4 format) in the script's directory
2. Run the script: `python poster_maker_root.py`

The script will process all MP4 files in the current directory and its subdirectories, creating a '0.jpg' poster image for each video.

## fasttranslate_root_60s_srt_files_to_vtt.py

This script uses Google Cloud Translation API to translate SRT files to English and Vietnamese, converting them to VTT format in the process.

### Key Features:
- Translates SRT files to both English and Vietnamese
- Converts SRT format to VTT format
- Uses multithreading for faster processing
- Implements a 60-second timeout for each file

### Usage:
1. Set up Google Cloud credentials (GOOGLE_APPLICATION_CREDENTIALS)
2. Place SRT files alongside MP4 files in the script's directory
3. Run the script: `python fasttranslate_root_60s_srt_files_to_vtt.py`

The script will process all SRT files associated with MP4 files, creating '_en.vtt' and '_vn.vtt' files for each.

## translate_srt_files.py

This script is similar to the previous one but focuses on translating SRT files without converting to VTT format.

### Key Features:
- Translates SRT files to both English and Vietnamese
- Maintains SRT format
- Uses Google Cloud Translation API

### Usage:
1. Set up Google Cloud credentials (GOOGLE_APPLICATION_CREDENTIALS)
2. Update the `folder_path` variable in the script to point to your SRT files
3. Run the script: `python translate_srt_files.py`

The script will process all SRT files in the specified folder, creating '_en.srt' and '_vn.srt' files for each.

## Setup and Dependencies

To use these scripts, you'll need to install the following Python packages:

```
pip install opencv-python numpy requests google-cloud-translate tqdm
```

For the Google Cloud Translation API scripts, you'll need to set up a Google Cloud project and obtain credentials. Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to your credentials file.

## Note

These scripts are designed to work together in a pipeline for processing movie subtitles. Ensure that you have the necessary permissions and licenses for the content you're translating and processing.

