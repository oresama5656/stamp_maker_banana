from PIL import Image, ImageDraw

def create_test_image():
    # Total size for 4x2 grid (e.g., 370*4 x 320*2 = 1480 x 640)
    # Standard LINE stamp size (max): 370x320 (main), but let's just use a simple size for testing.
    # Let's say each stamp is 200x200, so 800x400 total.
    width = 800
    height = 400
    cell_w = width // 4
    cell_h = height // 2
    
    # Create image with Magenta background
    img = Image.new('RGB', (width, height), color=(255, 0, 255))
    draw = ImageDraw.Draw(img)
    
    # Draw some content in each cell
    for row in range(2):
        for col in range(4):
            x = col * cell_w
            y = row * cell_h
            
            # Draw a circle in the center of the cell
            center_x = x + cell_w // 2
            center_y = y + cell_h // 2
            radius = 50
            draw.ellipse(
                (center_x - radius, center_y - radius, center_x + radius, center_y + radius),
                fill=(0, 255, 0), # Green circle
                outline=(0, 0, 0)
            )
            
            # Draw text or number
            draw.text((x + 10, y + 10), f"{row}-{col}", fill=(0, 0, 0))

    # Save to input folder
    img.save('input/test_sheet.png')
    print("Created input/test_sheet.png")

if __name__ == "__main__":
    create_test_image()
