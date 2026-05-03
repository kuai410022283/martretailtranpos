import os
from PIL import Image, ImageDraw

def create_icon():
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Green background (Rounded square approximation)
    # Draw a rectangle and 4 circles for corners
    color = '#4CAF50'
    r = 40
    w, h = size, size
    padding = 10
    
    # Main body
    draw.rectangle((padding+r, padding, w-padding-r, h-padding), fill=color)
    draw.rectangle((padding, padding+r, w-padding, h-padding-r), fill=color)
    
    # Corners
    draw.ellipse((padding, padding, padding+r*2, padding+r*2), fill=color)
    draw.ellipse((w-padding-r*2, padding, w-padding, padding+r*2), fill=color)
    draw.ellipse((padding, h-padding-r*2, padding+r*2, h-padding), fill=color)
    draw.ellipse((w-padding-r*2, h-padding-r*2, w-padding, h-padding), fill=color)
    
    # White Shopping Cart Icon
    cart_color = 'white'
    
    # Cart Handle
    # Start (60, 60)
    points = [
        (60, 70), (80, 70), (100, 150), (180, 150), (200, 90), (90, 90)
    ]
    
    # Draw lines manually for thickness
    thickness = 12
    
    # Handle to Basket
    draw.line([(60, 70), (80, 70)], fill=cart_color, width=thickness)
    draw.line([(80, 70), (100, 150)], fill=cart_color, width=thickness)
    
    # Basket Bottom
    draw.line([(100, 150), (180, 150)], fill=cart_color, width=thickness)
    
    # Basket Front
    draw.line([(180, 150), (200, 90)], fill=cart_color, width=thickness)
    
    # Basket Top
    draw.line([(200, 90), (90, 90)], fill=cart_color, width=thickness)
    
    # Wheels
    wheel_y = 180
    wheel_r = 14
    draw.ellipse((100-wheel_r, wheel_y-wheel_r, 100+wheel_r, wheel_y+wheel_r), fill=cart_color)
    draw.ellipse((180-wheel_r, wheel_y-wheel_r, 180+wheel_r, wheel_y+wheel_r), fill=cart_color)
    
    # Ensure directory exists
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    resources_dir = os.path.join(base_dir, 'resources')
    if not os.path.exists(resources_dir):
        os.makedirs(resources_dir)
        
    icons_dir = os.path.join(resources_dir, 'icons')
    if not os.path.exists(icons_dir):
        os.makedirs(icons_dir)
    
    # Save as PNG
    png_path = os.path.join(resources_dir, 'icon.png')
    img.save(png_path)
    print(f"Generated {png_path}")
    
    # Save as ICO
    ico_path = os.path.join(icons_dir, 'app.ico')
    img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(f"Generated {ico_path}")

if __name__ == '__main__':
    create_icon()
