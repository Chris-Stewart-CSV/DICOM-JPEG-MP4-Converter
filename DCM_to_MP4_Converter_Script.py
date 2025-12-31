# Can convert multi-frame DICOM (.dcm) files into video (.mp4)
# Currently tries to process all files at once, fine if processing only a few videos

# Issues:
# Currently there is an issue with frame alignment [ ]
# If run on single-frame DICOM files it will combine them into a video [x]
# Very memory hungry due to parallel processing [ ]

#Optimizations:
# TODO - change behavior to sequential in case user wants to process a lot of videos [ ]

import os
import cv2
import numpy as np
from pydicom import dcmread
from concurrent.futures import ProcessPoolExecutor

# --- Configuration ---
INPUT_ROOT = r"C:/Users/kingc/Desktop/DCM2JPG/Original-DCM-Video-Files"
OUTPUT_ROOT = r"C:/Users/kingc/Desktop/DCM2JPG/Converted-MP4-Files"
FPS = 15
MAX_WORKERS = 4 

os.makedirs(OUTPUT_ROOT, exist_ok=True)

def normalize_image(pixel_array):
    """Normalize DICOM data to 8-bit."""
    img_min, img_max = pixel_array.min(), pixel_array.max()
    if img_max == img_min:
        return np.zeros(pixel_array.shape, dtype=np.uint8)
    return ((pixel_array - img_min) / (img_max - img_min) * 255.0).astype(np.uint8)

def convert_single_dcm_to_mp4(dicom_path, output_filename):
    """Takes ONE .dcm file and creates ONE .mp4 file."""
    try:
        ds = dcmread(dicom_path)
        pixel_data = ds.pixel_array
        
        # DICOMs can be 2D (one image) or 3D (a stack/video)
        # We ensure we are working with a list of frames
        if len(pixel_data.shape) == 2:
            frames = [pixel_data]
        elif len(pixel_data.shape) == 3:
            # Check if it's (Frames, H, W) or (H, W, Channels)
            # Medical stacks are usually (Frames, H, W)
            frames = [pixel_data[i] for i in range(pixel_data.shape[0])]
        else:
            frames = [pixel_data]

        if not frames:
            return f"No frames found in {output_filename}"

        # Get dimensions from the first frame
        normalized_first_frame = normalize_image(frames[0])
        height, width = normalized_first_frame.shape[:2]
        
        video_path = os.path.join(OUTPUT_ROOT, f"{output_filename}.mp4")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(video_path, fourcc, FPS, (width, height), isColor=False)

        for f in frames:
            out.write(normalize_image(f))
        
        out.release()
        return f"Converted: {output_filename}.mp4"

    except Exception as e:
        return f"Failed {output_filename}: {str(e)}"

def main():
    # Gather every single .dcm file in the directory
    # If you want to include subfolders, we use os.walk
    all_files = []
    for root, _, files in os.walk(INPUT_ROOT):
        for f in files:
            if f.lower().endswith(".dcm"):
                full_path = os.path.join(root, f)
                # Use the filename (without .dcm) as the video name
                clean_name = os.path.splitext(f)[0]
                all_files.append((full_path, clean_name))

    if not all_files:
        print(f"No .dcm files found in {INPUT_ROOT}")
        return

    print(f"Starting parallel conversion of {len(all_files)} individual files...")

    # Parallel processing: each file gets its own worker
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(convert_single_dcm_to_mp4, path, name) for path, name in all_files]
        
        for future in futures:
            print(future.result())

if __name__ == "__main__":
    main()

