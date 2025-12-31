import os
from pydicom import dcmread
from PIL import Image

# --- Configuration ---
DICOM_DIR = "directory/to/your/dcm/files/here" # Folder with .dcm files
OUTPUT_DIR = "directory/to/your/desired/output/folder/here" # Where to save JPEGs

# --- Create Output Folder if it doesn't exist ---
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Conversion Function ---
def convert_dicom_to_jpeg(dicom_path, output_path):
    try:
        ds = dcmread(dicom_path) # Read DICOM file
        image_array = ds.pixel_array # Get pixel data
        image = Image.fromarray(image_array) # Create PIL Image
        image.save(output_path, quality=90) # Save as JPEG (adjust quality 0-100)
        print(f"Converted: {dicom_path} -> {output_path}")
    except Exception as e:
        print(f"Error converting {dicom_path}: {e}")

# --- Main Processing Loop ---
for root, _, files in os.walk(DICOM_DIR):
    for filename in files:
        if filename.endswith(".dcm"):
            dicom_filepath = os.path.join(root, filename)
            # Generate JPEG filename (e.g., image.dcm -> image.jpg)
            jpeg_filename = os.path.splitext(filename)[0] + ".jpg"
            output_filepath = os.path.join(OUTPUT_DIR, jpeg_filename)
            convert_dicom_to_jpeg(dicom_filepath, output_filepath)

print("Conversion complete!")