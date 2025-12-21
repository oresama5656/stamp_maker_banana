import os
import sys
import math
from PIL import Image

def process_image(file_path, output_dir, tolerance=30):
    """
    Splits a 4x2 stamp sheet into 8 images and applies chroma key transparency.
    """
    try:
        img = Image.open(file_path)
        img = img.convert("RGBA")
    except Exception as e:
        print(f"Error opening {file_path}: {e}")
        return

    width, height = img.size
    cell_w = width // 4
    cell_h = height // 2

    filename = os.path.splitext(os.path.basename(file_path))[0]
    
    # Target color: Magenta (255, 0, 255)
    target_r, target_g, target_b = 255, 0, 255

    count = 1
    for row in range(2):
        for col in range(4):
            left = col * cell_w
            top = row * cell_h
            right = left + cell_w
            bottom = top + cell_h
            
            # Crop the individual stamp
            crop = img.crop((left, top, right, bottom))
            
            # Process transparency
            datas = crop.getdata()
            new_data = []
            
            # Optimization: If tolerance is 0, use exact match (faster)
            # But user requested tolerance, so we implement distance check.
            # Using squared Euclidean distance for performance (avoid sqrt)
            tol_sq = tolerance * tolerance * 3 # Rough approximation for RGB distance
            
            # Better approach for tolerance:
            # Check if each channel is within range.
            # Or use Euclidean distance in RGB space.
            # Let's use Euclidean distance: sqrt((r1-r2)^2 + ...) < tolerance
            
            for item in datas:
                # item is (r, g, b, a)
                r, g, b = item[0], item[1], item[2]
                
                # Calculate distance to Magenta
                dist = math.sqrt((r - target_r)**2 + (g - target_g)**2 + (b - target_b)**2)
                
                if dist <= tolerance:
                    new_data.append((255, 255, 255, 0)) # Transparent
                else:
                    new_data.append(item)
            
            crop.putdata(new_data)
            
            # Save
            output_filename = f"{filename}_{count:02d}.png"
            output_path = os.path.join(output_dir, output_filename)
            crop.save(output_path, "PNG")
            print(f"Saved: {output_path}")
            
            count += 1

def main():
    input_dir = "input"
    output_dir = "output"
    
    # Default tolerance
    tolerance = 50
    
    # Simple argument parsing for tolerance
    if len(sys.argv) > 1:
        try:
            tolerance = int(sys.argv[1])
            print(f"Using tolerance: {tolerance}")
        except ValueError:
            print("Invalid tolerance value. Using default: 50")

    if not os.path.exists(input_dir):
        print(f"Error: '{input_dir}' directory not found.")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Supported extensions
    exts = ('.png', '.jpg', '.jpeg')
    
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(exts)]
    
    if not files:
        print(f"No images found in '{input_dir}'.")
        return

    print(f"Found {len(files)} images. Processing...")
    
    for f in files:
        file_path = os.path.join(input_dir, f)
        process_image(file_path, output_dir, tolerance)
        
    print("Done!")

if __name__ == "__main__":
    main()
