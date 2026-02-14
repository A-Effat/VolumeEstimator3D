# VolumeEstimator3D

A Python tool for annotating 2D image slices and estimating 3D volumes.

Although originally designed for ultrasound data, this tool is suitable for **any modality** where slice thickness is known and object boundaries can be annotated.

Examples include: ultrasound frames, CT slices, MRI sections, microscopy Z-stacks, and serial section images.

## Features
- Extract frames from video files or work with image sequences.
- Annotate selected slices using an interactive graphical interface.
- Calibrate with pixel-to-mm scaling.
- Estimate 3D volumes using **linear interpolation** between annotated slices.  
  The method applies the **trapezoidal rule**: averaging the areas of adjacent contours and multiplying by slice spacing.
- Export volume metrics and contours for downstream analysis or 3D visualization.

## Validation Data
When conducting validation:
- Sample Thickness: 1 mm
- Diameter or Edge of Square: 5 mm for reference
- Start and end frame should be the first and last frame (1-100); 99 frames in total
  
Expected Volumes:
- Circle: Radius = 2.5 mm; Diameter = 5 mm; Volume = 1943.86 mm³
- Square: Length = 5 mm; Volume = 2475 mm³
- Variable Circle: Average Radius = 2.5 mm; Average Diameter = 5 mm; Volume = 2105.98 mm³; will vary due to application of trapezoidal rule
## Sample Data

This repository includes a sample video:  
**`sample_video.avi`**  
Use it to test the full pipeline — from frame extraction to annotation and volume estimation.

> The sample has been anonymized and contains no personally identifying information.

### Sample Output (Expected Range)

When using `sample_video.avi` with a slice thickness of **0.076 mm**, expected results fall within:

| Metric                  | Expected Range         |
|-------------------------|------------------------|
| **Tumour Volume**       | 175 – 200 mm³          |
| **Max Width**           | 5.5 – 6.5 mm           |
| **Avg Width**           | 4.0 – 4.5 mm           |
| **Max Depth**           | ~5.0 mm                |
| **Avg Depth**           | 3.3 – 3.6 mm           |
| **Length**              | 13 – 14 mm             |
| **Pixel-to-mm Ratio**   | ~28                    |

> *Slight variation is expected due to manual annotation and calibration precision.*

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/A-Effat/VolumeEstimator3D.git
cd VolumeEstimator3D
pip install -r requirements.txt
