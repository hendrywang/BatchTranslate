import cv2
import os
import numpy as np
import moviepy.editor as mp
from moviepy.config import change_settings
import subprocess

# Set the path to FFmpeg (same as before)
def get_ffmpeg_path():
    try:
        result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return None

ffmpeg_path = get_ffmpeg_path()
if ffmpeg_path:
    change_settings({"FFMPEG_BINARY": ffmpeg_path})
else:
    print("FFmpeg not found. Please install FFmpeg and make sure it's in your system PATH.")
    exit(1)

def remove_subtitles(input_video, output_video, subtitle_y, subtitle_height, target_size_mb=10):
    input_video = os.path.normpath(input_video.strip())
    
    if not os.path.isfile(input_video):
        print(f"Error: Input file '{input_video}' does not exist.")
        return

    cap = cv2.VideoCapture(input_video)
    
    if not cap.isOpened():
        print(f"Error: Could not open video file '{input_video}'.")
        return

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"Video properties: {width}x{height} at {fps} FPS")

    temp_output = "temp_output.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))
    
    # Create a mask for the subtitle area
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[subtitle_y:subtitle_y+subtitle_height, :] = 255

    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        if frame_count % 100 == 0:
            print(f"Processed {frame_count} frames")

        # Perform inpainting
        result = cv2.inpaint(frame, mask, 3, cv2.INPAINT_TELEA)
        
        out.write(result)
    
    cap.release()
    out.release()
    cv2.destroyAllWindows()

    print(f"Processed a total of {frame_count} frames")
    
    print("Adding audio back and compressing video...")
    
    video = mp.VideoFileClip(input_video)
    audio = video.audio
    video_without_audio = mp.VideoFileClip(temp_output)
    final_video = video_without_audio.set_audio(audio)
    
    duration = video.duration
    target_bitrate = (target_size_mb * 8192) / duration  # in kbps
    
    final_video.write_videofile(output_video, 
                                codec='libx264', 
                                audio_codec='aac', 
                                bitrate=f"{int(target_bitrate)}k")
    
    video.close()
    video_without_audio.close()
    final_video.close()
    
    os.remove(temp_output)
    
    print(f"Subtitle removal complete. Compressed output with audio saved to {output_video}")

# Prompt user for input
input_video = input("Enter the name of the input video file: ")
output_video = input("Enter the name for the output video file: ")
subtitle_y = int(input("Enter the Y-coordinate where the subtitle starts (from top of the frame): "))
subtitle_height = int(input("Enter the height of the subtitle area: "))
target_size = float(input("Enter the target size of the output video in MB (e.g., 10 for 10MB): "))

# Run the subtitle removal function
remove_subtitles(input_video, output_video, subtitle_y, subtitle_height, target_size)