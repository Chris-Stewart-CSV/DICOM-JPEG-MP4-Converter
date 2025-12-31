# Can convert multi-frame DICOM (.dcm) files into video (.mp4)
# Currently tries to process all files at once, fine if processing only a few videos

# Issues:
# Currently there is an issue with frame alignment
# If run on single-frame DICOM files it will combine them into a video
# Very memory hungry due to parallel processing

#Optimizations:
# TODO - change behavior to sequential in case user wants to process a lot of videos

import os
import cv2
import numpy as np
from pydicom import dcmread
from concurrent.futures import ProcessPoolExecutor

# --- Configuration ---
INPUT_ROOT = r"C:/Users/kingc/Desktop/DCM2JPG/Original-DCM-Image-Files"
OUTPUT_ROOT = r"C:/Users/kingc/Desktop/DCM2JPG/Converted-MP4-Files"
FPS = 15 # Typical fps is between 10 & 20
MAX_WORKERS = 4 

os.makedirs(OUTPUT_ROOT, exist_ok=True)

def normalize_image(pixel_array):
    """Normalize 12/16-bit DICOM data to 8-bit for MP4 compatibility."""
    img_min, img_max = pixel_array.min(), pixel_array.max()
    if img_max == img_min:
        return np.zeros(pixel_array.shape, dtype=np.uint8)
    return ((pixel_array - img_min) / (img_max - img_min) * 255.0).astype(np.uint8)

def process_video_logic(folder_path, video_name):
    """Processes all DICOMs in a folder into a single MP4."""
    try:
        # Get and sort DICOM files
        dicom_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith(".dcm")])
        
        if not dicom_files:
            return None

        frames = []
        for f in dicom_files:
            ds = dcmread(os.path.join(folder_path, f))
            # Only extract pixel data and normalize
            frame = normalize_image(ds.pixel_array)
            frames.append(frame)

        if frames:
            height, width = frames[0].shape
            video_path = os.path.join(OUTPUT_ROOT, f"{video_name}.mp4")
            
            # Use 'mp4v' codec for standard MP4
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            # isColor=False because medical DICOMs are usually grayscale
            out = cv2.VideoWriter(video_path, fourcc, FPS, (width, height), isColor=False)
            
            for frame in frames:
                out.write(frame)
            out.release()
            
            return f"Successfully created: {video_name}.mp4 ({len(frames)} frames)"
            
    except Exception as e:
        return f"Error processing {video_name}: {e}"

def main():
    tasks = []

    # 1. Check Root
    root_files = [f for f in os.listdir(INPUT_ROOT) if f.lower().endswith(".dcm")]
    if root_files:
        tasks.append((INPUT_ROOT, "Main_Folder_Sequence"))

    # 2. Check Subfolders
    for entry in os.listdir(INPUT_ROOT):
        full_path = os.path.join(INPUT_ROOT, entry)
        if os.path.isdir(full_path):
            sub_files = [f for f in os.listdir(full_path) if f.lower().endswith(".dcm")]
            if sub_files:
                tasks.append((full_path, entry))

    if not tasks:
        print(f"No .dcm files found in {INPUT_ROOT}")
        return

    print(f"Converting {len(tasks)} video sequence(s) in parallel...")

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        futures = [executor.submit(process_video_logic, t[0], t[1]) for t in tasks]
        
        # Print results as they finish
        for future in futures:
            result = future.result()
            if result:
                print(result)

if __name__ == "__main__":
    main()
