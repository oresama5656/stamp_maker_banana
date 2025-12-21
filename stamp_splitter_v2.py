import cv2
import numpy as np
import os
import sys
import argparse
from collections import Counter

def detect_bg_color_cv(img):
    """
    Detects the background color by analyzing the 4 corners of the image.
    Returns the BGR color.
    """
    height, width = img.shape[:2]
    corners = [
        (0, 0),
        (width - 1, 0),
        (0, height - 1),
        (width - 1, height - 1)
    ]
    
    colors = []
    for x, y in corners:
        # img[y, x] returns array like [b, g, r] (or [b, g, r, a])
        pixel = img[y, x]
        # Take only first 3 channels (BGR)
        colors.append(tuple(pixel[:3]))
    
    # Find most common color
    most_common = Counter(colors).most_common(1)[0][0]
    return np.array(most_common, dtype=np.uint8)

def process_image_cv(file_path, output_dir, tolerance=30, erosion=1):
    """
    Splits a 4x2 stamp sheet and applies high-quality transparency using OpenCV.
    Automatically detects background color from corners.
    """
    try:
        img = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        if img is None:
            print(f"Error: Could not read {file_path}")
            return
    except Exception as e:
        print(f"Error opening {file_path}: {e}")
        return

    # Ensure 4 channels (BGRA)
    if img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    
    height, width = img.shape[:2]
    cell_w = width // 4
    cell_h = height // 2

    filename = os.path.splitext(os.path.basename(file_path))[0]
    
    # Auto-detect background color from the whole sheet's corners
    target_bgr = detect_bg_color_cv(img)
    print(f"Processing {filename}: Detected background BGR {target_bgr}")
    
    # Define range for chroma key
    # Fix: Cast to int16 to avoid uint8 wrap-around during subtraction/addition
    target_bgr_int = target_bgr.astype(np.int16)
    lower_bound = np.clip(target_bgr_int - tolerance, 0, 255).astype(np.uint8)
    upper_bound = np.clip(target_bgr_int + tolerance, 0, 255).astype(np.uint8)

    count = 1
    for row in range(2):
        for col in range(4):
            left = col * cell_w
            top = row * cell_h
            right = left + cell_w
            bottom = top + cell_h
            
            # Crop
            crop = img[top:bottom, left:right]
            
            # Create mask for background
            crop_bgr = crop[:, :, :3]
            bg_mask = cv2.inRange(crop_bgr, lower_bound, upper_bound)
            
            # Fringe Removal: Dilate the background mask
            if erosion > 0:
                kernel = np.ones((3, 3), np.uint8)
                bg_mask = cv2.dilate(bg_mask, kernel, iterations=erosion)
            
            # Create Alpha channel
            alpha = cv2.bitwise_not(bg_mask)
            
            # Apply alpha
            b, g, r, a = cv2.split(crop)
            final_alpha = cv2.bitwise_and(a, alpha)
            final_crop = cv2.merge([b, g, r, final_alpha])
            
            # Save
            output_filename = f"{filename}_{count:02d}.png"
            output_path = os.path.join(output_dir, output_filename)
            
            is_success, im_buf = cv2.imencode(".png", final_crop)
            if is_success:
                im_buf.tofile(output_path)
                print(f"Saved: {output_path}")
            else:
                print(f"Failed to save {output_path}")
            
            count += 1

def main():
    parser = argparse.ArgumentParser(description="Advanced Stamp Splitter (OpenCV)")
    parser.add_argument("--input", default="input", help="Input directory")
    parser.add_argument("--output", default="output_v2", help="Output directory")
    parser.add_argument("--tolerance", type=int, default=50, help="Color tolerance (0-255)")
    parser.add_argument("--erosion", type=int, default=1, help="Fringe removal strength (iterations). 0 to disable.")
    
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: '{args.input}' directory not found.")
        return

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    exts = ('.png', '.jpg', '.jpeg')
    files = [f for f in os.listdir(args.input) if f.lower().endswith(exts)]
    
    if not files:
        print(f"No images found in '{args.input}'.")
        return

    print(f"Processing {len(files)} images with OpenCV...")
    print(f"Tolerance: {args.tolerance}, Fringe Removal (Erosion): {args.erosion}")
    
    for f in files:
        file_path = os.path.join(args.input, f)
        process_image_cv(file_path, args.output, args.tolerance, args.erosion)
        
    print("Done!")

if __name__ == "__main__":
    main()
