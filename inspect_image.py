import cv2
import numpy as np

def inspect_image(path):
    print(f"Inspecting: {path}")
    img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if img is None:
        print("Failed to load image.")
        return

    height, width = img.shape[:2]
    print(f"Size: {width}x{height}, Channels: {img.shape[2]}")
    
    # Check corners
    corners = [(0, 0), (width-1, 0), (0, height-1), (width-1, height-1)]
    for x, y in corners:
        pixel = img[y, x]
        print(f"Pixel at ({x}, {y}): {pixel} (BGR/BGRA)")

if __name__ == "__main__":
    # Check one of the output files
    # Note: Filename might be slightly different depending on split order, but _01 is top-left.
    inspect_image("output_v2/Gemini_Generated_Image_atznphatznphatzn_01.png")
    inspect_image("output_v2/test_sheet_01.png")
