from PIL import Image, ImageDraw, ImageFont

def create_placeholder():
    img = Image.new('RGB', (800, 600), color = (73, 109, 137))
    d = ImageDraw.Draw(img)
    d.text((10,10), "Placeholder Cover", fill=(255,255,0))
    img.save('anthropic-engineering/cover.png')

if __name__ == "__main__":
    create_placeholder()
