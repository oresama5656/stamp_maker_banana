from PIL import Image, ImageDraw
import os

def create_bg_test_images():
    output_dir = "input_remover"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. White Background with Red Circle
    img1 = Image.new('RGB', (400, 400), color=(255, 255, 255))
    draw1 = ImageDraw.Draw(img1)
    draw1.ellipse((100, 100, 300, 300), fill=(255, 0, 0), outline=(0, 0, 0))
    img1.save(os.path.join(output_dir, 'test_white_bg.png'))
    print("Created test_white_bg.png")

    # 2. Blue Background with Yellow Square
    img2 = Image.new('RGB', (400, 400), color=(0, 0, 255))
    draw2 = ImageDraw.Draw(img2)
    draw2.rectangle((100, 100, 300, 300), fill=(255, 255, 0), outline=(0, 0, 0))
    img2.save(os.path.join(output_dir, 'test_blue_bg.png'))
    print("Created test_blue_bg.png")

    # 3. Noisy White Background (simulating scan/photo)
    # Just a slightly off-white background
    img3 = Image.new('RGB', (400, 400), color=(250, 250, 250)) # Not pure white
    draw3 = ImageDraw.Draw(img3)
    draw3.ellipse((100, 100, 300, 300), fill=(0, 255, 0), outline=(0, 0, 0))
    # Add some noise pixels in corners
    img3.putpixel((0, 0), (245, 245, 245))
    img3.putpixel((399, 0), (240, 240, 240))
    img3.save(os.path.join(output_dir, 'test_noisy_bg.png'))
    print("Created test_noisy_bg.png")

if __name__ == "__main__":
    create_bg_test_images()
