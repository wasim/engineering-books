from PIL import Image, ImageChops
import sys

def auto_crop(image_path, output_path):
    img = Image.open(image_path)
    
    # Convert to RGB if not already
    img = img.convert('RGB')
    
    # Get the background color (assume top-left pixel is background)
    bg = Image.new(img.mode, img.size, img.getpixel((0,0)))
    
    # Calculate difference between image and background
    diff = ImageChops.difference(img, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    
    # Get bounding box of the non-background area
    bbox = diff.getbbox()
    
    if bbox:
        # Add a small margin if needed, or just crop exactly
        # Let's crop exactly for now
        cropped = img.crop(bbox)
        cropped.save(output_path)
        print(f"Cropped image saved to {output_path}")
        print(f"Original size: {img.size}, Cropped size: {cropped.size}")
    else:
        print("Could not detect content to crop.")
        # Fallback: just copy
        img.save(output_path)

if __name__ == "__main__":
    auto_crop('anthropic-engineering/original_cover.png', 'anthropic-engineering/cover.png')
