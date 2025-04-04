# Author: Andrew Effat
# Email: andrew.effat@uhn.ca

# Import required classes
from frame_extractor import FrameExtractor
from frame_selector import FrameSelector
from tumour_annotator import TumourAnnotator
from volume_calculator import VolumeCalculator
from tkinter import filedialog, messagebox, simpledialog
from datetime import datetime
import os
import csv
import tkinter as tk
import logging

# Configure logging
logging.basicConfig(
    filename="app_error.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

if __name__ == "__main__":

    try:
        logging.info("Application is starting...")

        def get_user_inputs():
            """Launch a GUI to get the video folder path and slice thickness from the user."""
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo(
                "Instructions", 
                "In the next window, select the folder containing your video files."
            )
            folder_path = filedialog.askdirectory(title="Select Folder Containing Videos")
            root.destroy()

            if not folder_path:
                messagebox.showerror("Error", "No folder selected. Exiting.")
                return None, None, None

            root = tk.Tk()
            root.title("Slice Thickness Configuration")

            slice_thickness_mm = None
            same_thickness = None

            def on_confirm():
                nonlocal slice_thickness_mm, same_thickness
                try:
                    slice_thickness_mm = float(thickness_entry.get())
                    if slice_thickness_mm <= 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("Error", "Please enter a valid positive number.")
                    return

                same_thickness = checkbox_var.get()
                root.quit()

            tk.Label(root, text="Enter slice thickness (in mm):").pack(pady=5)
            thickness_entry = tk.Entry(root)
            thickness_entry.pack(pady=5)

            checkbox_var = tk.BooleanVar(value=True)
            tk.Checkbutton(root, text="Use same slice thickness for all videos", variable=checkbox_var).pack(pady=5)

            tk.Button(root, text="Confirm", command=on_confirm).pack(pady=10)
            root.mainloop()
            root.destroy()

            return folder_path, slice_thickness_mm, same_thickness
        
        

        folder_path, slice_thickness_mm, same_thickness = get_user_inputs()
        if not folder_path or slice_thickness_mm is None:
            exit()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_csv = os.path.join(folder_path, "tumour_volume_results_{}.csv".format(timestamp))
        with open(results_csv, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Video Name', 'Tumour Volume (mm^3)','Max Width (mm)', 'Avg Width (mm)', 'Max Depth (mm)', 'Avg Depth (mm)', 'Length (mm)', 'Slice Thickness (mm)', 'Pixel-to-mm Ratio', 'Timestamp'])

        for video_name in os.listdir(folder_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if video_name.endswith(('.avi', '.mp4', '.mov')):
                video_path = os.path.join(folder_path, video_name)
                video_name = os.path.splitext(video_name)[0]
                logging.info(f"Processing {video_name}...")

                # If "same thickness" is not checked, prompt user for slice thickness per video
                if not same_thickness:
                    application_window = tk.Tk()
                    application_window.withdraw()
                    application_window.title("Slice Thickness Configuration")
                    slice_thickness_mm = simpledialog.askfloat(
                        "Slice Thickness Configuration",
                        f"Enter slice thickness (in mm) for {video_name}:",
                        parent=application_window
                    )
                    if slice_thickness_mm is None:
                        messagebox.showerror("Error", "No slice thickness entered. Exiting.")
                        exit()
                    application_window.destroy()
                    

                output_dir = os.path.join(folder_path, f"{video_name}_frames_{timestamp}")
                os.makedirs(output_dir, exist_ok=True)

                frame_extractor = FrameExtractor(video_path, output_dir)
                total_frames = frame_extractor.extract_frames()
                logging.info(f"Total frames extracted: {total_frames}")

                frame_selector = FrameSelector(output_dir)
                sampled_frames = frame_selector.get_sampled_frames()
                logging.info(f"Sampled frames for annotation: {sampled_frames}")

                annotation_dir = os.path.join(folder_path, f"{video_name}_annotations_{timestamp}")
                os.makedirs(annotation_dir, exist_ok=True)  # Ensure directory exists before saving
                                    
                for idx, frame_path in enumerate(sampled_frames):
                    annotator = TumourAnnotator(frame_path, annotation_dir, idx, sampled_frames)
                    if idx == len(sampled_frames) - 1:  # Last frame
                        pixel_to_mm_ratio = annotator.get_pixel_to_mm_ratio()
                        if pixel_to_mm_ratio is None:
                            raise ValueError("Pixel-to-mm ratio not calculated.")

                logging.info("Annotation completed.")

                calculator = VolumeCalculator(
                    annotated_frames=sorted([os.path.join(annotation_dir, f) for f in os.listdir(annotation_dir) if f.endswith(".json")]),
                    output_dir=os.path.join(folder_path, f"{video_name}_calculated_{timestamp}"),
                    total_frames=total_frames,
                    slice_thickness_mm=slice_thickness_mm,
                    pixel_to_mm_ratio=pixel_to_mm_ratio,
                )
                volume_mm3, max_width, avg_width, max_depth, avg_depth, length = calculator.run()

                with open(results_csv, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([video_name, volume_mm3, max_width, avg_width, max_depth, avg_depth, length, slice_thickness_mm,pixel_to_mm_ratio,timestamp])
        
        logging.info(f"Results saved to {results_csv}")

    except Exception as e:
        logging.error("An error occurred", exc_info=True)
        messagebox.showerror("Critical Error", "Check app_error.log for details.")
