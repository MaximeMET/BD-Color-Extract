# -*- coding: utf-8 -*-
"""
Created on Wed Sep  4 18:47:23 2024

@author: maxim
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw
from collections import Counter, defaultdict
import colorsys
import numpy as np
import os

version = "beta"+" "+"20240913"
name = "BD_color_extract"

# Function: Calculate and set the window to be centered
def center_window(window):
    window.update_idletasks()    # Update window size and layout
    width = window.winfo_width()
    height = window.winfo_height()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = int((screen_width/2) - (width/0.5))
    y = int((screen_height/2) - (height/1))
    window.geometry(f'+{x}+{y}')

# Initialize main window
root = tk.Tk()
root.title(f"{name} {version}")

# Ensure the window is centered
center_window(root)
    
# Function: Open file dialog to select input image
def select_input_image():
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
    if file_path:
        input_image_entry.delete(0, tk.END)
        input_image_entry.insert(0, file_path)
        # Set output folder to the directory of the input image
        output_folder_entry.delete(0, tk.END)
        output_folder_entry.insert(0, os.path.dirname(file_path))

# Function: Open folder dialog to select output folder
def select_output_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        output_folder_entry.delete(0, tk.END)
        output_folder_entry.insert(0, folder_path)

def tone_separation(image, num_tones):
    img_array = np.array(image)
    img_array_normalized = img_array / 255.0
    interval = 1.0 / (num_tones - 1)
    quantized_img_array = np.round(img_array_normalized / interval) * interval
    quantized_img_array = np.uint8(quantized_img_array * 255)
    toned_image = Image.fromarray(quantized_img_array)
    return toned_image
        

def is_similar(color1, color2, threshold=10):
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
        
def calculate_hue(color):
    r, g, b = [x / 255.0 for x in color]
    h, _, _ = colorsys.rgb_to_hsv(r, g, b)
    return h * 360
                
# Function: Process the image
def process_image():
    input_path = input_image_entry.get()
    output_folder = output_folder_entry.get()
    output_filename = filename_entry.get()
    output_path = os.path.join(output_folder, f"{output_filename}.png")

    try:
        # Open the image file
        image = Image.open(input_path)
        image = image.convert('RGB')

        # Check image size and resize if necessary
        max_size = 2048
        width, height = image.size
        if min(width, height) > max_size:
            scaling_factor = max_size / min(width, height)
            new_width = int(width * scaling_factor)
            new_height = int(height * scaling_factor)
            image = image.resize((new_width, new_height), Image.LANCZOS)

        # Get user inputs
        merge_threshold = int(merge_threshold_entry.get())
        
        # Handle tone separation input
        try:
            num_tones_input = float(num_tones_entry.get())if tone_separation_var.get() else 256
            num_tones = min(max(int(round(num_tones_input)), 1), 256)  # 确保num_tones在1到256之间
        except ValueError:
            num_tones = 256

        output_image = tone_separation(image, num_tones) if tone_separation_var.get() else image
        # output_image.save('Seperate_image.png')

        colors = list(output_image.getdata())
        color_counter = Counter(colors)
        color_numbers = num_tones*num_tones if tone_separation_var.get() else 256*256
        top_colors = color_counter.most_common(color_numbers*color_numbers*color_numbers)
        top_colors = merge_similar_colors(top_colors, merge_threshold)

        hue_ranges = [(0, 30), (30, 90), (90, 150), (150, 240), (240, 300), (300, 360)]
        categorized_colors = defaultdict(list)

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
                    
        # Handle number of colors input
        try:
            num_color_input = float(max_coloum_number_entry.get())
            num_color_input = min(max(int(round(num_color_input)), 1), 256)  # 确保num_tones在1到256之间
        except ValueError:
            num_color_input = 256  # Default to 256 (no seperation)
        
        for category in categorized_colors:
            categorized_colors[category] = sort_colors_by_count(categorized_colors[category])[:num_color_input]

        sorted_categories = sorted(
            [cat for cat in categorized_colors if cat != 'grayscale'],
            key=lambda x: calculate_hue(categorized_colors[x][0][0])
        )
        if 'grayscale' in categorized_colors:
            sorted_categories.append('grayscale')

        block_size = 128
        max_blocks = max(len(categorized_colors[category]) for category in sorted_categories)
        canvas_width = max_blocks * block_size
        canvas_height = len(sorted_categories) * block_size

        canvas = Image.new('RGB', (canvas_width, canvas_height), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)

        for i, category in enumerate(sorted_categories):
            colors = categorized_colors[category]
            for j, (color, count) in enumerate(colors):
                top_left_corner = (j * block_size, i * block_size)
                bottom_right_corner = ((j + 1) * block_size, (i + 1) * block_size)
                draw.rectangle([top_left_corner, bottom_right_corner], fill=color)

        canvas.save(output_path)
        
        if show_image_var.get():
            canvas.show()
        
        message_label.config(text=f"Image processing completed! Output file saved at: {output_path}")
        # messagebox.showinfo("完成", "图像处理完成！")

    except Exception as e:
        messagebox.showerror("Error!", f"Error occurred while processing the image: {e}")

# Function: Toggle display of the tone separation input field
def toggle_num_tones_entry():
    if tone_separation_var.get():
        num_tones_label.grid()
        num_tones_entry.grid()
    else:
        num_tones_label.grid_remove()
        num_tones_entry.grid_remove()
    
# Input image path
input_image_label = tk.Label(root, text="Input Image Path:")
input_image_label.grid(row=0, column=0, padx=10, pady=10, sticky='ew')
input_image_entry = tk.Entry(root, width=50)
input_image_entry.grid(row=0, column=1, padx=10, pady=10, sticky='ew')
input_image_button = tk.Button(root, text="...", command=select_input_image, width=10)
input_image_button.grid(row=0, column=2, padx=10, pady=10)

# Output folder path
output_folder_label = tk.Label(root, text="Output Folder Path:")
output_folder_label.grid(row=1, column=0, padx=10, pady=10, sticky='ew')
output_folder_entry = tk.Entry(root, width=50)
output_folder_entry.grid(row=1, column=1, padx=10, pady=10, sticky='ew')
output_folder_button = tk.Button(root, text="...", command=select_output_folder, width=10)
output_folder_button.grid(row=1, column=2, padx=10, pady=10)

# Output filename
filename_label = tk.Label(root, text="Output Filename:")
filename_label.grid(row=2, column=0, padx=10, pady=10, sticky='ew')
filename_entry = tk.Entry(root, width=50)
filename_entry.grid(row=2, column=1, padx=10, pady=10, sticky='ew')
filename_entry.insert(0, "extracted_colors")  # 默认文件名

# Merge threshold
merge_threshold_label = tk.Label(root, text="Merge Similar Colors Threshold:")
merge_threshold_label.grid(row=3, column=0, padx=10, pady=10, sticky='ew')
merge_threshold_entry = tk.Entry(root, width=50)
merge_threshold_entry.grid(row=3, column=1, padx=10, pady=10, sticky='ew')
merge_threshold_entry.insert(0, "64")  # 默认值为64

# Tone separation checkbox
tone_separation_var = tk.BooleanVar(value=True)
tone_separation_check = tk.Checkbutton(root, text="Tone Seperation", variable=tone_separation_var, command=toggle_num_tones_entry)
tone_separation_check.grid(row=4, column=0, padx=10, pady=10, columnspan=2, sticky='ew')
# Number of tones for tone separation
num_tones_label = tk.Label(root, text="Number of Tones (2-256):")
num_tones_label.grid(row=5, column=0, padx=10, pady=10, sticky='ew')
num_tones_entry = tk.Entry(root, width=50)
num_tones_entry.grid(row=5, column=1, padx=10, pady=10, sticky='ew')
num_tones_entry.insert(0, "32")  # 默认值为32

# Max number of colors
max_coloum_number_label = tk.Label(root, text="Number of Colors Per Row")
max_coloum_number_label.grid(row=6, column=0, padx=10, pady=10, sticky='ew')
max_coloum_number_entry = tk.Entry(root, width=50)
max_coloum_number_entry.grid(row=6, column=1, padx=10, pady=10, sticky='ew')
max_coloum_number_entry.insert(0, "6")  # 默认值为6

# Display image checkbox
show_image_var = tk.BooleanVar(value=True)
show_image_check = tk.Checkbutton(root, text="Show Image", variable=show_image_var)
show_image_check.grid(row=7, column=0, padx=10, pady=10, columnspan=2, sticky='ew')

# Process image button
process_button = tk.Button(root, text="Process Image", command=process_image, height=2, width=50)
process_button.grid(row=8, column=1, padx=10, pady=10, sticky='ew')

# Status message
message_label = tk.Label(root, text="", fg="black")
message_label.grid(row=9, column=0, columnspan=4, padx=10, pady=10)

root.mainloop()
