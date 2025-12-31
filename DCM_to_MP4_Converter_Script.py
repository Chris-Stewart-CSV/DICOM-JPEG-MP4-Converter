# Can convert multi-frame DICOM (.dcm) files into video (.mp4)
# Currently tries to process all files at once, fine if processing only a few videos

# Issues:
# Currently there is an issue with frame alignment [x]
# If run on single-frame DICOM files it will combine them into a video [x]
# Very memory hungry due to parallel processing [ ]

#Optimizations:
# TODO - change behavior to sequential in case user wants to process a lot of videos [x]
# TODO - OpenCV is picky about DICOM - implement buffered copy approach [ ]

import os
import cv2
import numpy as np
from pydicom import dcmread

# --- Configuration ---
INPUT_ROOT = r"C:/Users/kingc/Desktop/DCM2JPG/Original-DCM-Video-Files"
OUTPUT_ROOT = r"C:/Users/kingc/Desktop/DCM2JPG/Converted-MP4-Files"
FPS = 15

os.makedirs(OUTPUT_ROOT, exist_ok=True)

def normalize_image(pixel_array):
    """Normalize DICOM data and ensure it is memory-contiguous for OpenCV."""
    img_min, img_max = pixel_array.min(), pixel_array.max()
    
    if img_max == img_min:
        return np.zeros(pixel_array.shape[:2], dtype=np.uint8)
    
    normalized = ((pixel_array - img_min) / (img_max - img_min) * 255.0).astype(np.uint8)
    return np.ascontiguousarray(normalized)

def convert_single_dcm_to_mp4(dicom_path, output_filename):
    """Takes ONE .dcm file and creates ONE .mp4 file."""
    try:
        ds = dcmread(dicom_path)
        pixel_data = ds.pixel_array
        
        # Determine if file is single-frame (2D) or multi-frame (3D)
        if len(pixel_data.shape) == 2:
            frames = [pixel_data]
        elif len(pixel_data.shape) == 3:
            frames = [pixel_data[i] for i in range(pixel_data.shape[0])]
        else:
            frames = [pixel_data]

        if not frames:
            return "No frames found"

        # Initialize video properties based on the first frame
        sample_frame = normalize_image(frames[0])
        height, width = sample_frame.shape[:2]
        
        video_path = os.path.join(OUTPUT_ROOT, f"{output_filename}.mp4")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(video_path, fourcc, FPS, (width, height), isColor=False)

        for f in frames:
            cleaned_frame = normalize_image(f)
            if cleaned_frame.shape[:2] != (height, width):
                cleaned_frame = cv2.resize(cleaned_frame, (width, height))
            out.write(cleaned_frame)
        
        out.release()
        return "Complete"

    except Exception as e:
        return f"Failed: {str(e)}"

def main():
    # Gather all files
    all_files = []
    for root, _, files in os.walk(INPUT_ROOT):
        for f in files:
            if f.lower().endswith(".dcm"):
                all_files.append((os.path.join(root, f), f))

    if not all_files:
        print(f"No .dcm files found in {INPUT_ROOT}")
        return

    print(f"Found {len(all_files)} files. Starting sequential processing...\n")

    # Sequential Loop (One by one)
    for i, (full_path, filename) in enumerate(all_files, 1):
        clean_name = os.path.splitext(filename)[0]
        
        # Log the start of processing
        print(f"[{i}/{len(all_files)}] {filename} - processing...", end=" ", flush=True)
        
        # Execute conversion
        result = convert_single_dcm_to_mp4(full_path, clean_name)
        
        # Log the result
        print(f"{result}")

    print("\nAll files have been processed!")

if __name__ == "__main__":
    main()
