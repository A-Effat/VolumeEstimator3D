# Author: Andrew Effat
# Email: andrew.effat@uhn.ca

import numpy as np
import json
import os


class VolumeCalculator:
    def __init__(self, annotated_frames, output_dir, total_frames, slice_thickness_mm, pixel_to_mm_ratio):
        """
        annotated_frames: List of paths to annotated frames (JSON files).
        output_dir: Directory to save extrapolated frames.
        total_frames: Total number of frames to extrapolate over.
        slice_thickness_mm: Thickness between slices in mm.
        pixel_to_mm_ratio: Pixel-to-mm conversion ratio.
        """
        self.annotated_frames = annotated_frames
        self.output_dir = output_dir
        self.total_frames = total_frames
        self.slice_thickness_mm = slice_thickness_mm
        self.pixel_to_mm_ratio = pixel_to_mm_ratio
        # Create a unique subfolder for each run

        os.makedirs(self.output_dir, exist_ok=True)

    def load_annotations(self):
        """Load annotated points from JSON files."""
        annotations = {}
        for frame_path in self.annotated_frames:
            frame_number = int(os.path.basename(frame_path).split('_')[1].split('.')[0])
            with open(frame_path, 'r') as f:
                data = json.load(f)
            annotations[frame_number] = np.array(data['points'])
        return annotations


    def calculate_volume(self, areas, frame_indices):
        """Estimate the tumor volume using the trapezoidal rule."""
        volume = 0
        for i in range(len(areas) - 1):
            frame_distance = (frame_indices[i + 1] - frame_indices[i]) * self.slice_thickness_mm
            volume += (areas[i] + areas[i + 1]) / 2 * frame_distance
        
        volume_mm3 = volume / (self.pixel_to_mm_ratio ** 2)  # Convert pixels² to mm²
        return volume, volume_mm3
    def calculate_width_depth_per_frame(self, annotations):
        """Calculate width and depth for each frame."""
        frame_metrics = {}
        for frame_number, points in annotations.items():
            x_coords = points[:, 0]
            y_coords = points[:, 1]
            width = (max(x_coords) - min(x_coords))/self.pixel_to_mm_ratio
            depth = (max(y_coords) - min(y_coords))/self.pixel_to_mm_ratio
            frame_metrics[frame_number] = {'width': width, 'depth': depth}
        return frame_metrics

    def aggregate_width_depth(self, frame_metrics):
        """Aggregate maximum and average width and depth across frames."""
        widths = [metrics['width'] for metrics in frame_metrics.values()]
        depths = [metrics['depth'] for metrics in frame_metrics.values()]
        max_width = max(widths)
        avg_width = sum(widths) / len(widths)
        max_depth = max(depths)
        avg_depth = sum(depths) / len(depths)
        return max_width, avg_width, max_depth, avg_depth


    def run(self):
        """Run the extrapolation and volume estimation pipeline."""
        annotations = self.load_annotations()

        # Calculate areas of each  polygon
        frame_indices = sorted(annotations.keys())
        areas = [self.calculate_polygon_area(annotations[frame]) for frame in frame_indices]
        frame_metrics = self.calculate_width_depth_per_frame(annotations)
        max_width, avg_width, max_depth, avg_depth = self.aggregate_width_depth(frame_metrics)
        length = (frame_indices[-1] - frame_indices[0]) * self.slice_thickness_mm
        # Estimate tumor volume
        volume, volume_mm3 = self.calculate_volume(areas, frame_indices)
        print(f"Estimated tumor volume: {round(volume,3)} squared pixels * millimeters")
        print(f"Estimated tumor volume: {round(volume_mm3,3)} cubic millimeters")
        return (round(volume_mm3, 3),round(max_width, 3),round(avg_width, 3),round(max_depth, 3),round(avg_depth, 3),round(length, 3)
    )

    def calculate_polygon_area(self, coords):
        """Calculate area of a polygon given its vertices."""
        if not np.array_equal(coords[0], coords[-1]):  # Close polygon if not closed
            coords = np.vstack([coords, coords[0]])
        x = coords[:, 0]
        y = coords[:, 1]
        return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
    
    def ensure_closed_polygon(self, points):
        """Ensure the polygon is closed by appending the first point to the end if necessary."""
        if not np.array_equal(points[0], points[-1]):
            points = np.vstack([points, points[0]])
        #print(points[0],points[-1])
        return points
    
   






   



    
    
