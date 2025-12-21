import os
import sys
import argparse
from PIL import Image, ImageDraw
from collections import Counter

def detect_bg_color(img, tolerance=30):
    """
    Detects the background color by analyzing the 4 corners.
    Returns the most common color among the corners.
    """
    width, height = img.size
    corners = [
        (0, 0),
        (width - 1, 0),
        (0, height - 1),
        (width - 1, height - 1)
    ]
    
    colors = []
    for x, y in corners:
        colors.append(img.getpixel((x, y)))
    
    # Find the most common color
    # Note: With tolerance, this is tricky. 
    # For now, we assume the corners are exactly the same or very close.
    # If they vary slightly (noise), Counter might see them as different.
    # A simple approach: Just take the top-left as reference, 
    # but check if others are similar.
    
    # Let's count exact matches first
    most_common = Counter(colors).most_common(1)[0][0]
    return most_common

def is_color_similar(c1, c2, tolerance):
    """
    Checks if two colors are similar within tolerance.
    """
    # Handle RGBA vs RGB
    c1 = c1[:3]
    c2 = c2[:3]
    
    dist_sq = sum((a - b) ** 2 for a, b in zip(c1, c2))
    return dist_sq <= (tolerance * tolerance * 3)

def process_flood_fill(img, tolerance=30):
    """
    Removes background using flood fill starting from corners.
    Smartly checks all 4 corners.
    """
    img = img.convert("RGBA")
    width, height = img.size
    
    # Detect dominant background color from corners
    bg_ref = detect_bg_color(img)
    
    corners = [
        (0, 0),
        (width - 1, 0),
        (0, height - 1),
        (width - 1, height - 1)
    ]
    
    # Flood fill from any corner that matches the reference background color
    for corner in corners:
        pixel_color = img.getpixel(corner)
        if is_color_similar(pixel_color, bg_ref, tolerance):
            try:
                ImageDraw.floodfill(img, xy=corner, value=(0, 0, 0, 0), thresh=tolerance)
            except Exception:
                pass
                
    return img

def process_auto_color_key(img, tolerance=30):
    """
    Detects background color from corners and removes it GLOBALLY.
    (Good for removing 'donut holes' but risky for inner details).
    """
    img = img.convert("RGBA")
    
    # Detect background color
    bg_ref = detect_bg_color(img)
    print(f"  Detected background color: {bg_ref}")
    
    datas = img.getdata()
    new_data = []
    
    tr, tg, tb = bg_ref[:3]
    tol_sq = tolerance * tolerance * 3
    
    for item in datas:
        r, g, b = item[0], item[1], item[2]
        dist_sq = (r - tr)**2 + (g - tg)**2 + (b - tb)**2
        
        if dist_sq <= tol_sq:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
            
    img.putdata(new_data)
    return img

def main():
    parser = argparse.ArgumentParser(description="Background Removal Tool")
    parser.add_argument("--mode", choices=["flood", "color", "auto_color"], default="flood", 
                        help="Mode: 'flood' (connected from corners), 'color' (manual specific color), 'auto_color' (detect color from corners and remove globally)")
    parser.add_argument("--tolerance", type=int, default=30, help="Tolerance (0-255)")
    parser.add_argument("--color", type=str, default="255,255,255", help="Target RGB for 'color' mode")
    parser.add_argument("--input", default="input_remover", help="Input directory")
    parser.add_argument("--output", default="output_remover", help="Output directory")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input directory '{args.input}' not found.")
        return
        
    if not os.path.exists(args.output):
        os.makedirs(args.output)
        
    # Parse manual target color if needed
    target_color = (255, 255, 255)
    if args.mode == "color":
        try:
            target_color = tuple(map(int, args.color.split(',')))
        except:
            print("Error: Invalid color format.")
            return

    exts = ('.png', '.jpg', '.jpeg')
    files = [f for f in os.listdir(args.input) if f.lower().endswith(exts)]
    
    if not files:
        print(f"No images found in '{args.input}'.")
        return
        
    print(f"Processing {len(files)} images. Mode: {args.mode}, Tolerance: {args.tolerance}")
    
    for f in files:
        file_path = os.path.join(args.input, f)
        try:
            img = Image.open(file_path)
            
            if args.mode == "flood":
                # Auto-detects from corners and floods connected areas
                result = process_flood_fill(img, args.tolerance)
            elif args.mode == "auto_color":
                # Auto-detects from corners and removes globally
                result = process_auto_color_key(img, args.tolerance)
            else:
                # Manual color key
                # Re-use the logic from auto_color but with manual target
                # (Need to refactor slightly or just duplicate logic for simplicity here)
                # Let's just call a helper or do it inline.
                # Actually process_auto_color_key uses detected color.
                # Let's make a generic function.
                
                # Inline for manual color:
                img = img.convert("RGBA")
                datas = img.getdata()
                new_data = []
                tr, tg, tb = target_color
                tol_sq = args.tolerance * args.tolerance * 3
                for item in datas:
                    r, g, b = item[0], item[1], item[2]
                    if ((r - tr)**2 + (g - tg)**2 + (b - tb)**2) <= tol_sq:
                        new_data.append((255, 255, 255, 0))
                    else:
                        new_data.append(item)
                img.putdata(new_data)
                result = img
                
            output_filename = os.path.splitext(f)[0] + "_processed.png"
            output_path = os.path.join(args.output, output_filename)
            result.save(output_path, "PNG")
            print(f"Saved: {output_path}")
            
        except Exception as e:
            print(f"Failed to process {f}: {e}")
            
    print("Done!")

if __name__ == "__main__":
    main()
