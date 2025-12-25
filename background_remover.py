import cv2
import numpy as np
import os
import argparse
from collections import Counter

def detect_bg_color_cv(img):
    """
    Detects background color from 4 corners using OpenCV.
    Returns BGR numpy array.
    """
    height, width = img.shape[:2]
    corners = [
        img[0, 0],
        img[0, width-1],
        img[height-1, 0],
        img[height-1, width-1]
    ]
    
    # Filter out alpha if present (though we usually use BGR for detection)
    corners_bgr = [c[:3] for c in corners]
    
    # Convert to tuple for Counter
    corners_tuple = [tuple(c) for c in corners_bgr]
    most_common = Counter(corners_tuple).most_common(1)[0][0]
    return np.array(most_common, dtype=np.uint8)

def process_remover(input_dir, output_dir, mode="flood", tolerance=30, color="255,255,255", erosion=0):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Parse manual target color
    target_bgr = None
    if mode == "color":
        try:
            rgb = list(map(int, color.split(',')))
            target_bgr = np.array(rgb[::-1], dtype=np.uint8) # RGB to BGR
        except:
            print("Error: Invalid color format. Use R,G,B")
            return

    exts = ('.png', '.jpg', '.jpeg')
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(exts)]
    
    if not files:
        print(f"No images found in '{input_dir}'.")
        return
        
    print(f"Processing {len(files)} images. Mode: {mode}, Tolerance: {tolerance}, Erosion: {erosion}")
    
    for f in files:
        file_path = os.path.join(input_dir, f)
        try:
            # Read image
            img = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
            if img is None: continue

            # Ensure 4 channels (BGRA)
            if img.shape[2] == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
            
            # Determine background color
            if mode == "color":
                bg_color = target_bgr
            else:
                bg_color = detect_bg_color_cv(img)

            # Create Mask
            # 1. Color Key / Auto Color (Global)
            bg_color_int = bg_color.astype(np.int16)
            lower = np.clip(bg_color_int - tolerance, 0, 255).astype(np.uint8)
            upper = np.clip(bg_color_int + tolerance, 0, 255).astype(np.uint8)
            
            img_bgr = img[:, :, :3]
            mask = cv2.inRange(img_bgr, lower, upper)
            
            # 2. Flood Fill (Connected components from corners)
            if mode == "flood":
                # Create a mask for floodFill (h+2, w+2)
                h, w = img.shape[:2]
                flood_mask = np.zeros((h+2, w+2), np.uint8)
                
                # Flood fill from corners on the MASK itself? 
                # No, floodFill works on the image. 
                # Strategy: Flood fill the original image's background to a specific key color, 
                # or create a mask where flood filled areas are marked.
                
                # Better approach for "Flood" mode in OpenCV:
                # Use the mask we generated (which has ALL pixels of that color).
                # Then find connected components connected to the corners.
                
                # Find connected components on the mask
                num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=4)
                
                # Check corners of the labels
                corner_labels = set()
                corner_labels.add(labels[0, 0])
                corner_labels.add(labels[0, w-1])
                corner_labels.add(labels[h-1, 0])
                corner_labels.add(labels[h-1, w-1])
                
                # Create new mask only for these labels
                final_mask = np.zeros_like(mask)
                for label in corner_labels:
                    if label == 0: continue # Label 0 is usually background (black in mask), but here mask is 255 for BG color.
                    # Wait, inRange returns 255 for match. So background is white (255).
                    # connectedComponents treats 0 as background.
                    # So we want components that are 255.
                    final_mask[labels == label] = 255
                
                mask = final_mask

            # Erosion (Fringe Removal)
            # Dilate the BACKGROUND mask = Erode the FOREGROUND
            if erosion > 0:
                kernel = np.ones((3, 3), np.uint8)
                mask = cv2.dilate(mask, kernel, iterations=erosion)

            # Apply Alpha
            alpha = cv2.bitwise_not(mask)
            
            # Combine
            b, g, r, a = cv2.split(img)
            final_alpha = cv2.bitwise_and(a, alpha)
            final_img = cv2.merge([b, g, r, final_alpha])
            
            output_filename = os.path.splitext(f)[0] + "_processed.png"
            output_path = os.path.join(output_dir, output_filename)
            
            is_success, im_buf = cv2.imencode(".png", final_img)
            if is_success:
                im_buf.tofile(output_path)
                print(f"Saved: {output_path}")
            
        except Exception as e:
            print(f"Failed to process {f}: {e}")
            import traceback
            traceback.print_exc()
            
    print("Done!")

def main():
    parser = argparse.ArgumentParser(description="Background Removal Tool (OpenCV)")
    parser.add_argument("--mode", choices=["flood", "color", "auto_color"], default="flood", 
                        help="Mode: 'flood' (connected), 'color' (manual), 'auto_color' (global)")
    parser.add_argument("--tolerance", type=int, default=30, help="Tolerance (0-255)")
    parser.add_argument("--erosion", type=int, default=0, help="Erosion/Fringe Removal (0-10)")
    parser.add_argument("--color", type=str, default="255,255,255", help="Target RGB for 'color' mode")
    parser.add_argument("--input", default="input_remover", help="Input directory")
    parser.add_argument("--output", default="output_remover", help="Output directory")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input directory '{args.input}' not found.")
        return
        
    process_remover(args.input, args.output, args.mode, args.tolerance, args.color, args.erosion)

if __name__ == "__main__":
    main()
