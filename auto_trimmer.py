import cv2
import numpy as np
import os
import argparse

def auto_trim(file_path, output_dir, padding=10):
    """
    Automatically crops the image to the non-transparent content with padding.
    """
    try:
        # Read image with alpha channel
        img = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        if img is None:
            print(f"Error: Could not read {file_path}")
            return
    except Exception as e:
        print(f"Error opening {file_path}: {e}")
        return

    # Check if image has alpha channel
    if img.shape[2] != 4:
        print(f"Skipping {file_path}: No alpha channel found.")
        return

    # Extract alpha channel
    alpha = img[:, :, 3]

    # Find all non-zero points (non-transparent)
    points = cv2.findNonZero(alpha)

    if points is None:
        print(f"Skipping {file_path}: Image is fully transparent.")
        return

    # Get bounding rect
    x, y, w, h = cv2.boundingRect(points)

    # Add padding
    height, width = img.shape[:2]
    
    x_start = max(0, x - padding)
    y_start = max(0, y - padding)
    x_end = min(width, x + w + padding)
    y_end = min(height, y + h + padding)

    # Crop
    cropped = img[y_start:y_end, x_start:x_end]

    # Save
    filename = os.path.splitext(os.path.basename(file_path))[0]
    output_filename = f"{filename}_trimmed.png"
    output_path = os.path.join(output_dir, output_filename)

    is_success, im_buf = cv2.imencode(".png", cropped)
    if is_success:
        im_buf.tofile(output_path)
        print(f"Saved: {output_path} (Size: {x_end-x_start}x{y_end-y_start})")
    else:
        print(f"Failed to save {output_path}")

def process_auto_trimmer(input_dir, output_dir, padding=10):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    exts = ('.png', '.jpg', '.jpeg')
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(exts)]
    
    if not files:
        print(f"No images found in '{input_dir}'.")
        return

    print(f"Processing {len(files)} images with padding {padding}...")
    
    for f in files:
        file_path = os.path.join(input_dir, f)
        auto_trim(file_path, output_dir, padding)
        
    print("Done!")

def main():
    parser = argparse.ArgumentParser(description="Auto Trimmer (Crop Transparent Area)")
    parser.add_argument("--input", default="input_trim", help="Input directory")
    parser.add_argument("--output", default="output_trim", help="Output directory")
    parser.add_argument("--padding", type=int, default=10, help="Padding around the content in pixels")
    
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: '{args.input}' directory not found.")
        return

    process_auto_trimmer(args.input, args.output, args.padding)

if __name__ == "__main__":
    main()
