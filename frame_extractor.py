# Author: Andrew Effat
# Email: andrew.effat@uhn.ca

import cv2
import os

class FrameExtractor:
    
    def __init__(self, video_path, output_dir, frame_rate=1):
        self.video_path = video_path
        self.output_dir = output_dir
        self.frame_rate = frame_rate
    
    def extract_frames(self):
        os.makedirs(self.output_dir, exist_ok=True)
        cap = cv2.VideoCapture(self.video_path)
        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imwrite(f"{self.output_dir}/frame_{frame_count:04d}.png", frame)
            frame_count += 1
        cap.release()
        return frame_count
