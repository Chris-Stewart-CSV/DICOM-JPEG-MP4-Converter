# Can convert multi-frame DICOM (.dcm) files into video (.mp4)
# Currently tries to process all files at once, fine if processing only a few videos

# Issues:
# Currently there is an issue with frame alignment [x]
# If run on single-frame DICOM files it will combine them into a video [x]
# Very memory hungry due to parallel processing [x]

#Optimizations:
# TODO - change behavior to sequential in case user wants to process a lot of videos [x]
# TODO - OpenCV is picky about DICOM - implement buffered copy [x]

import os
import cv2
import numpy as np
from pydicom import dcmread

# --- Configuration ---
INPUT_ROOT = r"C:/Users/kingc/Desktop/DCM2JPG/Original-DCM-Video-Files"
OUTPUT_ROOT = r"C:/Users/kingc/Desktop/DCM2JPG/Converted-MP4-Files"
FPS = 15

os.makedirs(OUTPUT_ROOT, exist_ok=True)

def normalize_to_8bit(pixel_array):
    """Normalize and force copy into a fresh 8-bit memory buffer."""
    img_min, img_max = pixel_array.min(), pixel_array.max()
    
    if img_max == img_min:
        return np.zeros(pixel_array.shape[:2], dtype=np.uint8)
    
    # Perform the math
    norm = ((pixel_array - img_min) / (img_max - img_min) * 255.0).astype(np.float32)
    
    # Create a completely fresh 8-bit buffer (Clean Canvas)
    # This specifically targets the 'minstep' memory error
    dst = np.empty(pixel_array.shape[:2], dtype=np.uint8)
    np.copyto(dst, norm.astype(np.uint8))
    
    return dst

def convert_single_dcm_to_mp4(dicom_path, output_filename):
    try:
        ds = dcmread(dicom_path)
        pixel_data = ds.pixel_array
        
        # Handle Multi-frame vs Single-frame
        if len(pixel_data.shape) == 2:
            raw_frames = [pixel_data]
        elif len(pixel_data.shape) == 3:
            raw_frames = [pixel_data[i] for i in range(pixel_data.shape[0])]
        else:
            raw_frames = [pixel_data]

        # Prepare first frame to get dimensions
        first_frame = normalize_to_8bit(raw_frames[0])
        height, width = first_frame.shape
        
        video_path = os.path.join(OUTPUT_ROOT, f"{output_filename}.mp4")
        # Define codec - using 'XVID' as a fallback if 'mp4v' still struggles
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(video_path, fourcc, FPS, (width, height), isColor=False)

        if not out.isOpened():
            return "Error: Writer could not open."

        for f in raw_frames:
            # Process frame into the clean buffer
            frame_8bit = normalize_to_8bit(f)
            
            # Final safety check on dimensions
            if frame_8bit.shape != (height, width):
                frame_8bit = cv2.resize(frame_8bit, (width, height))
                
            out.write(frame_8bit)
        
        out.release()
        return "Complete"

    except Exception as e:
        return f"Failed: {str(e)}"

def main():
    # Identify files
    all_files = [f for f in os.listdir(INPUT_ROOT) if f.lower().endswith(".dcm")]

    if not all_files:
        print(f"No .dcm files found in {INPUT_ROOT}")
        return

    print(f"Found {len(all_files)} files. Starting clean-buffer sequential processing...\n")

    for i, filename in enumerate(all_files, 1):
        full_path = os.path.join(INPUT_ROOT, filename)
        clean_name = os.path.splitext(filename)[0]
        
        print(f"[{i}/{len(all_files)}] {filename} - processing...", end=" ", flush=True)
        
        result = convert_single_dcm_to_mp4(full_path, clean_name)
        print(f"{result}")

    print("\nAll tasks finished.")

if __name__ == "__main__":
    main()
