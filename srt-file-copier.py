import os
import shutil
from tqdm import tqdm

def copy_srt_files():
    # Get the current working directory
    source_dir = os.getcwd()
    
    # Create the destination directory
    destination_dir = os.path.join(source_dir, "SRT_files")
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    # Get the total number of .srt files
    total_files = sum([len(files) for r, d, files in os.walk(source_dir) if any(f.endswith('.srt') for f in files)])

    # Create a progress bar
    with tqdm(total=total_files, unit='file') as pbar:
        # Walk through the source directory
        for root, dirs, files in os.walk(source_dir):
            # Skip the SRT_files directory
            if "SRT_files" in dirs:
                dirs.remove("SRT_files")
            
            # Filter for .srt files
            srt_files = [f for f in files if f.endswith('.srt')]
            
            for file in srt_files:
                # Get the full path of the source file
                src_path = os.path.join(root, file)
                
                # Create the corresponding path in the destination directory
                rel_path = os.path.relpath(root, source_dir)
                dest_path = os.path.join(destination_dir, rel_path)
                
                # Create the destination directory if it doesn't exist
                if not os.path.exists(dest_path):
                    os.makedirs(dest_path)
                
                # Copy the file
                shutil.copy2(src_path, dest_path)
                
                # Update the progress bar
                pbar.update(1)

    print(f"All SRT files have been copied to {destination_dir}")

if __name__ == "__main__":
    copy_srt_files()