#!/usr/bin/env python3
"""
Script to create a dummy banner image for gdsync
Run this once to generate resources/banner.png
"""

import os
from PIL import Image, ImageDraw, ImageFont

def create_dummy_banner():
    # Create resources directory if it doesn't exist
    os.makedirs('resources', exist_ok=True)
    
    # Banner dimensions
    width, height = 580, 120
    
    # Create image with gradient background
    img = Image.new('RGB', (width, height), color='#2c3e50')
    draw = ImageDraw.Draw(img)
    
    # Create gradient effect
    for y in range(height):
        color_value = int(44 + (y / height) * 30)  # Gradient from #2c3e50 to lighter
        color = (color_value, color_value + 20, color_value + 30)
        draw.line([(0, y), (width, y)], fill=color)
    
    # Try to use a system font, fallback to default
    try:
        font_large = ImageFont.truetype("arial.ttf", 36)
        font_small = ImageFont.truetype("arial.ttf", 16)
    except:
        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 36)
            font_small = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
    
    # Get version from environment variable (GitHub release tag) or use default
    version = os.environ.get('GITHUB_REF_NAME', 'v3.0')
    if version.startswith('refs/tags/'):
        version = version.replace('refs/tags/', '')
    
    # Add text
    title_text = "GDSYNC"
    subtitle_text = "GDSync by MalikHw47"
    version_text = version
    
    # Calculate text positions for centering
    title_bbox = draw.textbbox((0, 0), title_text, font=font_large)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) // 2
    
    subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=font_small)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_x = (width - subtitle_width) // 2
    
    version_bbox = draw.textbbox((0, 0), version_text, font=font_small)
    version_width = version_bbox[2] - version_bbox[0]
    version_x = (width - version_width) // 2
    
    # Draw text with shadow effect
    shadow_offset = 2
    
    # Title shadow
    draw.text((title_x + shadow_offset, 20 + shadow_offset), title_text, 
              fill='#000000', font=font_large)
    # Title
    draw.text((title_x, 20), title_text, fill='#ecf0f1', font=font_large)
    
    # Subtitle shadow
    draw.text((subtitle_x + shadow_offset, 65 + shadow_offset), subtitle_text, 
              fill='#000000', font=font_small)
    # Subtitle
    draw.text((subtitle_x, 65), subtitle_text, fill='#bdc3c7', font=font_small)
    
    # Version shadow
    draw.text((version_x + shadow_offset, 90 + shadow_offset), version_text, 
              fill='#000000', font=font_small)
    # Version
    draw.text((version_x, 90), version_text, fill='#95a5a6', font=font_small)
    
    # Add decorative elements
    # Left and right borders
    draw.rectangle([0, 0, 5, height], fill='#3498db')
    draw.rectangle([width-5, 0, width, height], fill='#3498db')
    
    # Top and bottom borders
    draw.rectangle([0, 0, width, 3], fill='#3498db')
    draw.rectangle([0, height-3, width, height], fill='#3498db')
    
    # Save the image
    img.save('resources/banner.png', 'PNG')
    print("Dummy banner created at resources/banner.png")

if __name__ == "__main__":
    create_dummy_banner()
