from PIL import Image, ImageChops
import sys

def auto_crop(image_path, output_path, margin_percent=15):
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
        # Add generous margin around the detected content
        left, top, right, bottom = bbox
        width = right - left
        height = bottom - top
        
        # Calculate margin in pixels
        margin_x = int(width * margin_percent / 100)
        margin_y = int(height * margin_percent / 100)
        
        # Apply margin, ensuring we don't go outside image bounds
        left = max(0, left - margin_x)
        top = max(0, top - margin_y)
        right = min(img.width, right + margin_x)
        bottom = min(img.height, bottom + margin_y)
        
        cropped = img.crop((left, top, right, bottom))
        cropped.save(output_path)
        print(f"Cropped image saved to {output_path}")
        print(f"Original size: {img.size}, Cropped size: {cropped.size}")
        print(f"Applied {margin_percent}% margin")
    else:
        print("Could not detect content to crop.")
        # Fallback: just copy
        img.save(output_path)

if __name__ == "__main__":
    auto_crop('anthropic-engineering/original_cover.png', 'anthropic-engineering/cover.png')
