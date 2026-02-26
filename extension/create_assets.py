from PIL import Image, ImageDraw

def create_icon(size, filename):
    img = Image.new('RGB', (size, size), color = (41, 128, 185))
    d = ImageDraw.Draw(img)
    # Just a simple shield-like placeholder (a rectangle for now)
    d.rectangle([size//4, size//4, 3*size//4, 3*size//4], fill=(236, 240, 241))
    img.save(f'icons/{filename}')

if __name__ == '__main__':
    create_icon(16, 'shield-16.png')
    create_icon(48, 'shield-48.png')
    create_icon(128, 'shield-128.png')
    print("Icons generated successfully.")
