import cv2
import numpy as np
import os
import sys
import argparse
from collections import Counter

def detect_bg_color_cv(img):
    """
    Detects the background color by analyzing the top-left and top-right corners.
    左上と右上の2点のみを使用（左下・右下にスタンプ本体が来る場合を考慮）
    Returns the BGR color.
    """
    height, width = img.shape[:2]
    # 左上と右上のみを使用（スタンプ本体が左下・右下に見切れる場合を考慮）
    corners = [
        (0, 0),          # 左上
        (width - 1, 0),  # 右上
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

def process_image_cv(file_path, output_dir, tolerance=30, erosion=1, grid="auto", remove_bg=True):
    """
    Splits a stamp sheet.
    remove_bg: If True, applies high-quality transparency using OpenCV.
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
    
    # Determine grid
    rows, cols = 2, 4
    if grid == "3x3":
        rows, cols = 3, 3
    elif grid == "4x4":
        rows, cols = 4, 4
    elif grid == "4x2":
        rows, cols = 2, 4
    elif grid == "auto":
        # Simple aspect ratio check
        ratio = width / height
        if 0.8 <= ratio <= 1.2: # Square-ish
            # 正方形はデフォルトで3x3（4x4は明示的に--grid 4x4を指定した場合のみ）
            rows, cols = 3, 3
            print(f"Auto-detected 3x3 grid (Square)")
        else:
            rows, cols = 2, 4
            print(f"Auto-detected 4x2 grid (Aspect Ratio: {ratio:.2f})")

    cell_w = width // cols
    cell_h = height // rows

    filename = os.path.splitext(os.path.basename(file_path))[0]
    
    # Auto-detect background color from the whole sheet's corners (only if needed)
    target_bgr = None
    lower_bound = None
    upper_bound = None
    
    if remove_bg:
        target_bgr = detect_bg_color_cv(img)
        print(f"Processing {filename}: Detected background BGR {target_bgr}, Grid: {cols}x{rows}")
        
        # Define range for chroma key
        target_bgr_int = target_bgr.astype(np.int16)
        lower_bound = np.clip(target_bgr_int - tolerance, 0, 255).astype(np.uint8)
        upper_bound = np.clip(target_bgr_int + tolerance, 0, 255).astype(np.uint8)
    else:
        print(f"Processing {filename}: Grid: {cols}x{rows} (Background Removal Disabled)")

    count = 1
    for row in range(rows):
        for col in range(cols):
            left = col * cell_w
            top = row * cell_h
            right = left + cell_w
            bottom = top + cell_h
            
            # Crop
            crop = img[top:bottom, left:right]
            
            final_crop = crop
            
            if remove_bg:
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

def process_splitter(input_dir, output_dir, tolerance=50, erosion=1, grid="auto", remove_bg=True):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    exts = ('.png', '.jpg', '.jpeg')
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(exts)]
    
    if not files:
        print(f"No images found in '{input_dir}'.")
        return

    print(f"Processing {len(files)} images with OpenCV...")
    print(f"Tolerance: {tolerance}, Fringe Removal (Erosion): {erosion}, Grid: {grid}, Remove BG: {remove_bg}")
    
    for f in files:
        file_path = os.path.join(input_dir, f)
        process_image_cv(file_path, output_dir, tolerance, erosion, grid, remove_bg)
        
    print("Done!")

def main():
    parser = argparse.ArgumentParser(description="Advanced Stamp Splitter (OpenCV)")
    parser.add_argument("--input", default="input", help="Input directory")
    parser.add_argument("--output", default="output_v2", help="Output directory")
    parser.add_argument("--tolerance", type=int, default=50, help="Color tolerance (0-255)")
    parser.add_argument("--erosion", type=int, default=1, help="Fringe removal strength (iterations). 0 to disable.")
    parser.add_argument("--grid", choices=["auto", "4x2", "3x3", "4x4"], default="auto", help="Grid layout (default: auto)")
    parser.add_argument("--no_bg", action="store_true", help="Disable background removal")
    
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: '{args.input}' directory not found.")
        return

    process_splitter(args.input, args.output, args.tolerance, args.erosion, args.grid, remove_bg=not args.no_bg)

if __name__ == "__main__":
    main()
