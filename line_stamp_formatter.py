import cv2
import numpy as np
import os
import argparse
import shutil

def resize_and_pad(img, target_w, target_h, margin=0):
    """
    Resizes image to FIT within target dimensions, maintaining aspect ratio.
    余白なしでリサイズした画像そのまま出力（Compact方式）。
    marginは無視される（互換性のため引数は維持）。
    """
    h, w = img.shape[:2]
    
    # Scale factor - use min to FIT within target (contain mode)
    scale = min(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    # Ensure even dimensions (LINE stamp requirement)
    if new_w % 2 != 0: new_w -= 1
    if new_h % 2 != 0: new_h -= 1
    
    # Resize image - no canvas, just resize and return
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    return resized

def resize_exact(img, target_w, target_h):
    """
    Resizes image and places it on a canvas with EXACT target dimensions.
    tab.png用：正確に96x74pxなど指定サイズを保証する。
    """
    h, w = img.shape[:2]
    
    # Ensure 4 channels (BGRA)
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
    elif img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    
    # Scale factor - use min to FIT within target (contain mode)
    scale = min(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    # Ensure dimensions are at least 1
    new_w = max(1, new_w)
    new_h = max(1, new_h)
    
    # Resize image
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    # Create transparent canvas with exact target dimensions
    canvas = np.zeros((target_h, target_w, 4), dtype=np.uint8)
    
    # Center the resized image on canvas
    x_offset = (target_w - new_w) // 2
    y_offset = (target_h - new_h) // 2
    
    canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
    
    return canvas

def process_formatter(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    exts = ('.png', '.jpg', '.jpeg')
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(exts)]
    files.sort() # Ensure consistent order
    
    if not files:
        print(f"No images found in '{input_dir}'.")
        return

    print(f"Formatting {len(files)} images...")
    
    # Process all regular stamps (no limit)
    count = 1
    for f in files:
        file_path = os.path.join(input_dir, f)
        try:
            img = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
            if img is None: continue
            
            # Ensure 4 channels
            if img.shape[2] == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
            
            # Format: 370x320, margin 10
            formatted = resize_and_pad(img, 370, 320, margin=10)
            
            # Save as 01.png, 02.png...
            output_filename = f"{count:02d}.png"
            output_path = os.path.join(output_dir, output_filename)
            
            is_success, im_buf = cv2.imencode(".png", formatted)
            if is_success:
                im_buf.tofile(output_path)
                print(f"Saved: {output_path}")
            
            # Generate Main and Tab images from the first image (01.png)
            if count == 1:
                # Main: 240x240
                main_img = resize_and_pad(img, 240, 240, margin=0)
                main_path = os.path.join(output_dir, "main.png")
                cv2.imencode(".png", main_img)[1].tofile(main_path)
                print(f"Generated: {main_path}")
                
                # Tab: 96x74
                tab_img = resize_exact(img, 96, 74)
                tab_path = os.path.join(output_dir, "tab.png")
                cv2.imencode(".png", tab_img)[1].tofile(tab_path)
                print(f"Generated: {tab_path}")

        except Exception as e:
            print(f"Error processing {f}: {e}")
        
        count += 1

    print("Done!")

def main():
    parser = argparse.ArgumentParser(description="LINE Stamp Formatter")
    parser.add_argument("--input", default="input_format", help="Input directory")
    parser.add_argument("--output", default="output_format", help="Output directory")
    
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: '{args.input}' directory not found.")
        return

    process_formatter(args.input, args.output)

if __name__ == "__main__":
    main()
