# -*- coding: utf-8 -*-
"""
Created on Tue Sep  3 20:11:01 2024

@author: maxim
"""

from PIL import Image, ImageDraw
from collections import Counter, defaultdict
import colorsys
import numpy as np

# Open the image file
image = Image.open('Image2.png')
image = image.convert('RGB')

# Check the size of the image and scale if necessary
max_size = 2048
width, height = image.size
if min(width, height) > max_size:
    scaling_factor = max_size / min(width, height)
    new_width = int(width * scaling_factor)
    new_height = int(height * scaling_factor)
    image = image.resize((new_width, new_height), Image.LANCZOS)

def tone_separation(image, num_tones):
    # Convert the image to a numpy array
    img_array = np.array(image)

    # Normalize pixel values to [0, 1]
    img_array_normalized = img_array / 255.0

    # Calculate intervals for each tone level
    interval = 1.0 / (num_tones - 1)

    # Apply tone separation by mapping to the nearest tone level
    quantized_img_array = np.round(img_array_normalized / interval) * interval

    # Scale back to [0, 255]
    quantized_img_array = np.uint8(quantized_img_array * 255)

    # Convert back to an image
    toned_image = Image.fromarray(quantized_img_array)

    return toned_image

output_image = tone_separation(image, 32)  # tones
output_image.save('Seperate_image.png')

def is_similar(color1, color2, threshold=64):
    return np.linalg.norm(np.array(color1) - np.array(color2)) < threshold

def merge_similar_colors(colors, threshold=64):
    unique_colors = []
    for color, count in colors:
        merged = False
        for i, (unique_color, unique_count) in enumerate(unique_colors):
            if is_similar(color, unique_color, threshold):
                total_count = unique_count + count
                weighted_avg_color = tuple(np.round(
                    ((np.array(unique_color) * unique_count) + (np.array(color) * count)) / total_count
                ).astype(int))
                unique_colors[i] = (weighted_avg_color, total_count)
                merged = True
                break
        if not merged:
            unique_colors.append((color, count))
    return unique_colors

def sort_colors_by_count(colors):
    return sorted(colors, key=lambda x: x[1], reverse=True)

# Get color data
colors = list(output_image.getdata())

# Count the occurrences of each color and get the top 32*32 colors
color_counter = Counter(colors)
top_colors = color_counter.most_common(32768)

# Deduplicate and merge colors before categorizing
top_colors = merge_similar_colors(top_colors)

# Define hue ranges and category containers
hue_ranges = [(0, 30), (30, 90), (90, 150), (150, 240), (240, 300), (300, 360)]
categorized_colors = defaultdict(list)

def calculate_hue(color):
    r, g, b = [x / 255.0 for x in color]
    h, _, _ = colorsys.rgb_to_hsv(r, g, b)
    return h * 360

# Categorize colors
for color, count in top_colors:
    r, g, b = [x / 255.0 for x in color]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    h = h * 360

    if s * 100 <= 12 or v * 100 <= 12:
        categorized_colors['grayscale'].append((color, count))
    else:
        for i, (lower, upper) in enumerate(hue_ranges):
            if lower <= h < upper:
                categorized_colors[f'hue_{i+1}'].append((color, count))
                break

# Sort by count and limit to drawing the top 6 colors per category
for category in categorized_colors:
    categorized_colors[category] = sort_colors_by_count(categorized_colors[category])[:6]

# Sort categories based on the hue of the first color, with greyscale at the end
sorted_categories = sorted(
    [cat for cat in categorized_colors if cat != 'grayscale'],
    key=lambda x: calculate_hue(categorized_colors[x][0][0])
)
if 'grayscale' in categorized_colors:
    sorted_categories.append('grayscale')

# Calculate the actual canvas size
block_size = 128
max_blocks = max(len(categorized_colors[category]) for category in sorted_categories)
canvas_width = max_blocks * block_size
canvas_height = len(sorted_categories) * block_size

# Create a new image
canvas = Image.new('RGB', (canvas_width, canvas_height), (255, 255, 255))
draw = ImageDraw.Draw(canvas)

# Draw color blocks
for i, category in enumerate(sorted_categories):
    colors = categorized_colors[category]
    for j, (color, count) in enumerate(colors):
        top_left_corner = (j * block_size, i * block_size)
        bottom_right_corner = ((j + 1) * block_size, (i + 1) * block_size)
        draw.rectangle([top_left_corner, bottom_right_corner], fill=color)

# Save the generated image
canvas.save('output_image.png')
canvas.show()
