import cv2
import numpy as np
import os

def capture_frames(video_path, interval):
    video = cv2.VideoCapture(video_path)
    fps = video.get(cv2.CAP_PROP_FPS)
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps

    frames = []
    timestamps = np.arange(0, duration, interval)

    for timestamp in timestamps:
        video.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        success, frame = video.read()
        if success:
            frames.append((timestamp, frame))

    video.release()
    return frames

def detect_faces(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return faces

def select_best_frame(frames):
    best_frame = None
    max_face_area = 0

    for timestamp, frame in frames:
        faces = detect_faces(frame)
        if len(faces) > 0:
            for (x, y, w, h) in faces:
                face_area = w * h
                if face_area > max_face_area:
                    max_face_area = face_area
                    best_frame = (timestamp, frame)
                    
    return best_frame

def save_frame(frame, output_path):
    cv2.imwrite(output_path, frame)

def main(video_path, interval):
    frames = capture_frames(video_path, interval)
    best_frame_data = select_best_frame(frames)

    if best_frame_data:
        _, best_frame = best_frame_data
        output_path = os.path.join(os.path.dirname(video_path), '0.jpg')
        
        if os.path.exists(output_path):
            overwrite = input(f"The file {output_path} already exists. Do you want to overwrite it? (y/n): ").strip().lower()
            if overwrite != 'y':
                print('File not overwritten.')
                return
        
        save_frame(best_frame, output_path)
        print(f'Best screenshot saved at {output_path}')
    else:
        print('No suitable frame with a main character detected.')

if __name__ == '__main__':
    video_path = '1.mp4'
    interval = 5  # Capture a frame every 5 seconds

    main(video_path, interval)