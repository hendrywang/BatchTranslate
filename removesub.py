import cv2
import os
import numpy as np
import moviepy.editor as mp
from moviepy.config import change_settings
import subprocess

# Set the path to FFmpeg
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
    # Normalize and clean up the input file path
    input_video = os.path.normpath(input_video.strip())
    
    # Check if input file exists
    if not os.path.isfile(input_video):
        print(f"Error: Input file '{input_video}' does not exist.")
        return

    # Open the video file
    cap = cv2.VideoCapture(input_video)
    
    # Check if video opened successfully
    if not cap.isOpened():
        print(f"Error: Could not open video file '{input_video}'.")
        return

    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"Video properties: {width}x{height} at {fps} FPS")

    # Create a temporary file for the video without audio
    temp_output = "temp_output.mp4"

    # Create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))
    
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        if frame_count % 100 == 0:
            print(f"Processed {frame_count} frames")

        # Create a full-size mask for the subtitle area
        mask = np.zeros((height, width), dtype=np.uint8)
        mask[subtitle_y:subtitle_y+subtitle_height, :] = 255
        
        # Inpaint the subtitle region
        frame = cv2.inpaint(frame, mask, 3, cv2.INPAINT_TELEA)
        
        # Write the processed frame
        out.write(frame)
    
    # Release resources
    cap.release()
    out.release()
    cv2.destroyAllWindows()

    print(f"Processed a total of {frame_count} frames")
    
    # Now let's add back the audio and compress the video
    print("Adding audio back and compressing video...")
    
    # Load the original video to extract audio
    video = mp.VideoFileClip(input_video)
    
    # Extract the audio
    audio = video.audio
    
    # Load the video without audio that we just created
    video_without_audio = mp.VideoFileClip(temp_output)
    
    # Add the audio back to the video
    final_video = video_without_audio.set_audio(audio)
    
    # Calculate bitrate for target file size
    duration = video.duration
    target_bitrate = (target_size_mb * 8192) / duration  # in kbps
    
    # Write the final video with audio and compression
    final_video.write_videofile(output_video, 
                                codec='libx264', 
                                audio_codec='aac', 
                                bitrate=f"{int(target_bitrate)}k")
    
    # Close the video files
    video.close()
    video_without_audio.close()
    final_video.close()
    
    # Remove the temporary file
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