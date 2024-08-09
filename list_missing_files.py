import os
from tqdm import tqdm

def check_files(root_dir='.'):
    missing_files = {
        'missing_srt': [],
        'missing_en_vtt': [],
        'missing_vn_vtt': []
    }
    small_files = []

    total_files = sum([len(files) for _, _, files in os.walk(root_dir)])

    with tqdm(total=total_files, desc="Processing files") as pbar:
        for folder, _, files in os.walk(root_dir):
            mp4_files = {os.path.splitext(file)[0] for file in files if file.endswith('.mp4')}
            srt_files = {os.path.splitext(file)[0] for file in files if file.endswith('.srt')}
            en_vtt_files = {os.path.splitext(file)[0].replace('_en', '') for file in files if file.endswith('_en.vtt')}
            vn_vtt_files = {os.path.splitext(file)[0].replace('_vn', '') for file in files if file.endswith('_vn.vtt')}

            for mp4_file in mp4_files:
                if mp4_file not in srt_files:
                    missing_files['missing_srt'].append(os.path.join(folder, mp4_file + '.mp4'))
                if mp4_file not in en_vtt_files:
                    missing_files['missing_en_vtt'].append(os.path.join(folder, mp4_file + '.mp4'))
                if mp4_file not in vn_vtt_files:
                    missing_files['missing_vn_vtt'].append(os.path.join(folder, mp4_file + '.mp4'))
            
            for file in files:
                if file.endswith('.srt') or file.endswith('.vtt'):
                    file_path = os.path.join(folder, file)
                    if os.path.getsize(file_path) < 320:
                        small_files.append(file_path)
                
                pbar.update(1)

    return missing_files, small_files

def main():
    root_dir = os.getcwd()
    missing_files, small_files = check_files(root_dir)

    print("MP4 files without corresponding SRT files:")
    for file in missing_files['missing_srt']:
        print(file)

    print("\nMP4 files without corresponding *_en.vtt files:")
    for file in missing_files['missing_en_vtt']:
        print(file)

    print("\nMP4 files without corresponding *_vn.vtt files:")
    for file in missing_files['missing_vn_vtt']:
        print(file)

    print("\nSRT and VTT files smaller than 1024 bytes:")
    for file in small_files:
        print(file)

if __name__ == "__main__":
    main()