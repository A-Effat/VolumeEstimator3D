# Author: Andrew Effat
# Email: andrew.effat@uhn.ca

import tkinter as tk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
import json
import os

class TumourAnnotator:
    def __init__(self, frame_path, annotation_dir,current_frame_index,frame_paths):
        self.current_frame_index = current_frame_index
        self.frame_path = frame_path
        self.frame_paths = frame_paths
        self.annotation_dir = annotation_dir
        self.points = []
        self.measuring_5mm = False
        self.pixel_to_mm_ratio = None

        self.root = tk.Tk()
        self.root.title("Tumour Annotator")
        self.image_panel = tk.Label(self.root)
        self.image_panel.pack()

        # Controls
        self.controls_frame = tk.Frame(self.root)
        self.controls_frame.pack(pady=10)

        self.undo_button = tk.Button(self.controls_frame, text="Undo", command=self.undo_last_action, width=15)
        self.undo_button.pack(side="left", padx=5)

        self.next_button = tk.Button(self.controls_frame, text="Next Frame", command=self.next_frame, width=15)
        self.next_button.pack(side="left", padx=5)

        self.status_label = tk.Label(self.root, text="")
        self.status_label.pack(pady=5)

        # Image panel bindings for drawing
        self.image_panel.bind("<Button-1>", self.start_drawing)
        self.image_panel.bind("<B1-Motion>", self.draw)
        self.image_panel.bind("<ButtonRelease-1>", self.stop_drawing)

        self.load_frame(self.frame_path)

        self.root.mainloop()

    def load_frame(self, frame_path):
        """Load and display the current frame."""
        self.points = []  # Reset points for new frame
        self.img = cv2.imread(frame_path)
        
        if self.img is None:
            messagebox.showerror("Error", f"Cannot load image: {frame_path}")
            self.root.quit()
            return

        self.update_display_image()

    def update_display_image(self):
        """Update the displayed image after any change."""
        img_rgb = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)

        # Limit displayed image size to avoid overlapping UI
        max_width = 1000
        max_height = 500  # or less, depending on your layout

        # Preserve aspect ratio
        original_width, original_height = img_pil.size
        aspect_ratio = original_height / original_width

        target_width = max_width
        target_height = int(target_width * aspect_ratio)

        if target_height > max_height:
            target_height = max_height
            target_width = int(target_height / aspect_ratio)

        img_pil = img_pil.resize((target_width, target_height), Image.LANCZOS)

        
        # Persist the PhotoImage object to avoid garbage collection
        self.tk_image = ImageTk.PhotoImage(img_pil)
        self.image_panel.config(image=self.tk_image)
        self.image_panel.image = self.tk_image  # Keep a reference to avoid being garbage collected

    def save_annotation(self):
        """Save the annotation for the current frame."""
        annotation_name = os.path.basename(self.frame_path).replace('.png', '.json')
        annotation_path = os.path.join(self.annotation_dir, annotation_name)
        os.makedirs(self.annotation_dir, exist_ok=True)
        with open(annotation_path, 'w') as f:
            json.dump({"points": self.points}, f)
        print(f"Annotation saved for {annotation_name}")

    def next_frame(self):
        """Handle frame progression and ensure last frame calibration."""
        self.save_annotation()
        if self.current_frame_index < len(self.frame_paths) - 1:
            self.root.destroy()  # Proceed to next frame
        else:
            self.next_button.config(state=tk.DISABLED)  # Temporarily disable button
            self.measure_5mm_line()  # Transition to calibration mode
            self.next_button.config(state=tk.NORMAL)  # Reactivate with updated command

    def start_drawing(self, event):
        """Start drawing with corrected coordinates."""
        corrected_x, corrected_y = self.correct_coordinates(event.x, event.y)
        self.points = [(corrected_x, corrected_y)]

    def draw(self, event):
        """Draw a line with corrected coordinates."""
        corrected_x, corrected_y = self.correct_coordinates(event.x, event.y)
        if len(self.points) > 0:
            last_point = self.points[-1]
            self.points.append((corrected_x, corrected_y))
            cv2.line(self.img, last_point, (corrected_x, corrected_y), (0, 255, 0), 2)
            self.update_display_image()  # Refresh to show the line

    def correct_coordinates(self, x, y):
        """Correct the mouse coordinates for image scaling and centering."""
        widget_width = self.image_panel.winfo_width()
        widget_height = self.image_panel.winfo_height()

        img_width, img_height = self.tk_image.width(), self.tk_image.height()

        # Calculate scaling factor and offsets
        scale_x = self.img.shape[1] / img_width
        scale_y = self.img.shape[0] / img_height

        offset_x = (widget_width - img_width) // 2
        offset_y = (widget_height - img_height) // 2

        # Correct the coordinates
        corrected_x = int((x - offset_x) * scale_x)
        corrected_y = int((y - offset_y) * scale_y)

        # Ensure coordinates are within bounds
        corrected_x = max(0, min(corrected_x, self.img.shape[1] - 1))
        corrected_y = max(0, min(corrected_y, self.img.shape[0] - 1))

        return corrected_x, corrected_y

    def stop_drawing(self, event):
        pass

    def undo_last_action(self):
        """Undo the last drawn action."""
        self.points = []
        self.load_frame(self.frame_path)
        if self.measuring_5mm:
            self.measure_5mm_line()

    def get_pixel_to_mm_ratio(self):
        """Return the pixel-to-mm ratio after calibration."""
        return getattr(self, 'pixel_to_mm_ratio', None)
        
    def measure_5mm_line(self):
        """Enable the user to draw a 5mm calibration line with exactly two points."""
        self.measuring_5mm = True
        self.load_frame(self.frame_path)  # Reload the frame for calibration
        self.status_label.config(text="Click two points to draw a 5mm calibration line.")
        
        # Clear points and unbind any drawing events
        self.points = []  
        self.image_panel.unbind("<Button-1>")
        self.image_panel.unbind("<B1-Motion>")
        self.image_panel.unbind("<ButtonRelease-1>")

        # Define the calibration mode's click event
        def on_click(event):
            if len(self.points) < 2:
                corrected_x, corrected_y = self.correct_coordinates(event.x, event.y)
                self.points.append((corrected_x, corrected_y))
                self.display_point_feedback(corrected_x, corrected_y)

                if len(self.points) == 2:
                    self.draw_calibration_line()
                    self.calculate_pixel_to_mm_ratio()
                    self.image_panel.unbind("<Button-1>")  # Disable further clicks
                    self.status_label.config(text="Calibration complete. Click 'Done' to proceed.")
                    self.next_button.config(text="Done", command=self.exit_annotation)

        # Bind new click event for calibration
        self.image_panel.bind("<Button-1>", on_click)

    def display_point_feedback(self, x, y):
        """Draw a small circle or marker to indicate the clicked point."""
        cv2.circle(self.img, (x, y), 2, (0, 0, 255), -1)  # red marker
        self.update_display_image()

    def draw_calibration_line(self):
        """Draw a line between the two calibration points."""
        if len(self.points) == 2:
            x1, y1 = self.points[0]
            x2, y2 = self.points[1]
            cv2.line(self.img, (x1, y1), (x2, y2), (0,0, 255), 2)  # Red line for calibration
            self.update_display_image()

    def calculate_pixel_to_mm_ratio(self):
        """Calculate and display the pixel-to-mm ratio based on the calibration line."""
        x1, y1 = self.points[0]
        x2, y2 = self.points[1]
        pixel_distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        self.pixel_to_mm_ratio = round(pixel_distance / 5.0,3)  # Assuming 5mm real-world distance
        print(f"Pixel-to-mm ratio: {self.pixel_to_mm_ratio:.2f}")

    def exit_annotation(self):
        """Exit the annotation process after calibration is complete."""
        self.root.destroy()
        #self.root.quit()
        







