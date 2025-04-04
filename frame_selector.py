# Author: Andrew Effat
# Email: andrew.effat@uhn.ca

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import cv2
import numpy as np
import logging


class FrameSelector:
    def __init__(self, frames_folder, parent = None):
        self.frames_folder = frames_folder
        self.frames = sorted([f for f in os.listdir(frames_folder) if f.endswith(".png")])
        self.current_index = 0
        self.start_frame = None
        self.end_frame = None
        

        # Set up the main window
        self.root = tk.Tk()
        self.root.title("Frame Selector")
        self.root.geometry("1200x800")  # Adjust window size
  
        # Image panel
        self.image_panel = tk.Label(self.root)
        self.image_panel.pack(expand=True, fill="both")

        # Progress indicator
        self.progress_label = tk.Label(self.root, text=f"Frame 1 of {len(self.frames)}")
        self.progress_label.pack(pady=5)

        # Slider for navigation
        self.slider = tk.Scale(self.root, from_=1, to=len(self.frames),
                               orient="horizontal", command=self.slider_update, length=700)
        self.slider.pack(fill="none", pady=10)

        # Selected frames indicator
        self.selection_label = tk.Label(self.root, text="Start Frame: None | End Frame: None", font=("Helvetica", 12))
        self.selection_label.pack(pady=5)

        # Frame selection controls
        self.controls_frame = tk.Frame(self.root)
        self.controls_frame.pack(pady=10)

        # Rectangular buttons with consistent text visibility
        self.set_start_button = tk.Button(self.controls_frame, text="Set as Start",
                                          command=self.set_start_frame, width=15, height=2)
        self.set_start_button.pack(side="left", padx=10)

        self.set_end_button = tk.Button(self.controls_frame, text="Set as End",
                                        command=self.set_end_frame, width=15, height=2)
        self.set_end_button.pack(side="left", padx=10)

        self.confirm_button = tk.Button(self.controls_frame, text="Confirm",
                                        command=self.confirm_selection, width=15, height=2)
        self.confirm_button.pack(side="left", padx=10)

        # Display the first frame
        self.display_frame(self.current_index)
        self.root.mainloop()

    def display_frame(self, index):
        """Display the frame at the given index."""
        frame_path = os.path.join(self.frames_folder, self.frames[index])
        frame = cv2.imread(frame_path)
        if frame is None:
            messagebox.showerror("Error", f"Cannot load frame: {frame_path}")
            return

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(frame_rgb)

        # Define max display size
        max_width = 1000
        max_height = 500  # so buttons are visible

        # Original size
        original_width, original_height = img_pil.size
        aspect_ratio = original_height / original_width

        # Resize based on width, but don't exceed max height
        target_width = max_width
        target_height = int(target_width * aspect_ratio)

        if target_height > max_height:
            target_height = max_height
            target_width = int(target_height / aspect_ratio)

        img_pil = img_pil.resize((target_width, target_height), Image.LANCZOS)


        img_tk = ImageTk.PhotoImage(img_pil)

        # Persist the reference to prevent garbage collection
        self.image_panel.config(image=img_tk)
        self.image_panel.image = img_tk  # Store reference in the widget to keep it alive

        # Update progress label
        self.progress_label.config(text=f"Frame {index + 1} of {len(self.frames)}")



    def slider_update(self, value):
        """Update the frame display based on slider position."""
        self.current_index = int(value) - 1  # Adjust to 0-based index for internal logic
        self.display_frame(self.current_index)

    def set_start_frame(self):
        """Set the current frame as the start frame."""
        self.start_frame = self.current_index
        self.update_selection_label()
        logging.info(f"Start frame set to {self.start_frame + 1}")

    def set_end_frame(self):
        """Set the current frame as the end frame."""
        self.end_frame = self.current_index
        self.update_selection_label()
        logging.info(f"End frame set to {self.end_frame + 1}")

    def update_selection_label(self):
        """Update the label showing the selected start and end frames."""
        start = self.start_frame + 1 if self.start_frame is not None else "None"
        end = self.end_frame + 1 if self.end_frame is not None else "None"
        self.selection_label.config(text=f"Start Frame: {start} | End Frame: {end}")

    def confirm_selection(self):
        """Confirm the selection of start and end frames."""
        if self.start_frame is not None and self.end_frame is not None:
            if self.start_frame < self.end_frame:
                with open("frame_selection.txt", "w") as f:
                    f.write(f"{self.start_frame},{self.end_frame}")
                logging.info("Start and end frames saved.")
                self.root.destroy()
            else:
                messagebox.showerror("Error", "Start frame must be less than the end frame.")
        else:
            messagebox.showerror("Error", "Please select both start and end frames.")

    def get_sampled_frames(self):
        """Get evenly sampled frames between start and end frames."""
        if self.start_frame is None or self.end_frame is None:
            raise ValueError("Start and end frames must be set before sampling.")
        
        total_frames = self.end_frame - self.start_frame + 1
        num_samples = max(2, int(total_frames * 0.1))  # Ensure at least 2 frames are selected

        # Select num_samples evenly spaced frames, including start and end      
        sampled_indices = np.linspace(self.start_frame, self.end_frame, num=num_samples, dtype=int)
        return [os.path.join(self.frames_folder, self.frames[i]) for i in sampled_indices]


if __name__ == "__main__":
    folder_path = filedialog.askdirectory(title="Select Folder Containing Frames")
    if folder_path:
        FrameSelector(folder_path)
