import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from PIL import Image, ImageTk, ImageFilter

version = "beta"+" "+"20240913"
name = "BD_color_scale"

# Function: Calculate and center the window
def center_window(window):
    window.update_idletasks()  # Update the size and layout of the window
    width = window.winfo_width()
    height = window.winfo_height()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = int((screen_width - width) / 2)
    y = int((screen_height - height) / 2)
    window.geometry(f'+{x}+{y}')
        
class ImageBlurApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{name} {version}")
        # Variables
        self.image_path_var = tk.StringVar()
        self.output_path_var = tk.StringVar()
        self.filename_var = tk.StringVar(value="color_results")
        self.gaussian_var = tk.BooleanVar(value=True)
        self.radius_var = tk.StringVar(value="0")  # Use StringVar for radius to handle empty input
        self.scan_direction_var = tk.StringVar(value="none")  # Initialize with "none"

        # Input image path
        tk.Label(root, text="Image address:").grid(row=0, column=0, sticky=tk.W)
        self.image_entry = tk.Entry(root, textvariable=self.image_path_var, width=50)
        self.image_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(root, text="...", command=self.browse_image).grid(row=0, column=2, padx=5, pady=5)

        # Output txt path
        tk.Label(root, text="Output file address:").grid(row=1, column=0, sticky=tk.W)
        self.output_entry = tk.Entry(root, textvariable=self.output_path_var, width=50)
        self.output_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Button(root, text="...", command=self.browse_output).grid(row=1, column=2, padx=5, pady=5)

        # Output filename
        tk.Label(root, text="Output file name:").grid(row=2, column=0, sticky=tk.W)
        self.filename_entry = tk.Entry(root, textvariable=self.filename_var, width=50)
        self.filename_entry.grid(row=2, column=1, padx=5, pady=5)

        # Gaussian blur toggle
        self.gaussian_check = tk.Checkbutton(root, text="Gaussian blur", variable=self.gaussian_var, command=self.toggle_blur)
        self.gaussian_check.grid(row=3, column=0, sticky=tk.W)

        # Blur radius input
        tk.Label(root, text="Blur radius:").grid(row=4, column=0, sticky=tk.W)
        self.radius_entry = tk.Entry(root, textvariable=self.radius_var, width=50)
        self.radius_entry.grid(row=4, column=1, padx=5, pady=5)
        self.radius_var.trace_add("write", self.update_preview)  # Bind update function to radius value changes

        # Scan direction
        tk.Label(root, text="Scanning Direction:").grid(row=5, column=0, sticky=tk.W)
        self.left_to_right = tk.Radiobutton(root, text="Left to right", variable=self.scan_direction_var, value="left_to_right")
        self.left_to_right.grid(row=6, column=0, sticky=tk.W)
        self.right_to_left = tk.Radiobutton(root, text="Right to left", variable=self.scan_direction_var, value="right_to_left")
        self.right_to_left.grid(row=7, column=0, sticky=tk.W)
        self.bottom_to_top = tk.Radiobutton(root, text="Bottom to top", variable=self.scan_direction_var, value="bottom_to_top")
        self.bottom_to_top.grid(row=8, column=0, sticky=tk.W)
        self.top_to_bottom = tk.Radiobutton(root, text="Top to bottom", variable=self.scan_direction_var, value="top_to_bottom")
        self.top_to_bottom.grid(row=9, column=0, sticky=tk.W)

        # Execute button
        tk.Button(root, text="Execute", command=self.execute_program).grid(row=10, column=0, columnspan=3, pady=5)
        
        # Message
        self.message_label = tk.Label(root, text="", fg="black")
        self.message_label.grid(row=11, column=0, columnspan=4, padx=10)

        # Image preview
        self.preview_label = tk.Label(root)
        self.preview_label.grid(row=1, column=3, rowspan=10, padx=10, pady=20)
        
        # Disable radius entry if Gaussian blur is not selected
        self.toggle_blur()

    def browse_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
        if file_path:
            self.image_path_var.set(file_path)
            folder_path = "/".join(file_path.split("/")[:-1])
            self.output_path_var.set(folder_path)
            self.update_preview()

            # Set initial scan direction based on image dimensions
            try:
                image = Image.open(file_path)
                width, height = image.size
                if width > height:
                    self.scan_direction_var.set("left_to_right")
                elif height > width:
                    self.scan_direction_var.set("bottom_to_top")
                else:
                    self.scan_direction_var.set("none")
            except Exception as e:
                messagebox.showerror("Error!", f"Unable to load image: {e}")

    def browse_output(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.output_path_var.set(folder_path)

    def toggle_blur(self):
        if self.gaussian_var.get():
            self.radius_entry.config(state="normal")
            self.update_preview()
        else:
            self.radius_entry.config(state="disabled")
            self.radius_var.set("0")  # Set default value for radius if blur is disabled

    def get_radius(self):
        try:
            radius = float(self.radius_var.get())
        except ValueError:
            radius = 0.0
        return radius

    def update_preview(self, *args):
        img_path = self.image_path_var.get()
        if img_path:
            try:
                image = Image.open(img_path)
                radius = self.get_radius()
                if self.gaussian_var.get():
                    image = image.filter(ImageFilter.GaussianBlur(radius))
                image = image.resize((256, 256), Image.Resampling.LANCZOS)
                img_tk = ImageTk.PhotoImage(image)
                self.preview_label.config(image=img_tk)
                self.preview_label.image = img_tk
            except Exception as e:
                messagebox.showerror("Error!", f"Unable to load image: {e}")

    def save_and_compute_averages(self, image, output_file):
        scan_direction = self.scan_direction_var.get()
        # Open image and get its original size
        original_width, original_height = image.size

        # Resize image to make output data lines be 256
        if original_width > original_height or (original_width == original_height and scan_direction == "left_to_right"):
            new_width = 256
            new_height = original_height
            image = image.resize((new_width, new_height))
            # print(f"图片宽大于高，调整后的图片大小: {new_width}x{new_height}")
        else:
            new_height = 256
            new_width = original_width
            image = image.resize((new_width, new_height))
            # print(f"图片高大于宽，调整后的图片大小: {new_width}x{new_height}")

        data_dict = {}

        if scan_direction == "left_to_right" or (scan_direction == "left_to_right" and original_width == original_height):
            for y in range(new_height):
                for x in range(new_width):
                    pixel = image.getpixel((x, y))
                    r, g, b, a = (pixel if len(pixel) == 4 else (*pixel, 255))
                    if x not in data_dict:
                        data_dict[x] = ([r], [g], [b], [a])
                    else:
                        data_dict[x][0].append(r)
                        data_dict[x][1].append(g)
                        data_dict[x][2].append(b)
                        data_dict[x][3].append(a)
        elif scan_direction == "right_to_left":
            for y in range(new_height):
                for x in range(new_width - 1, -1, -1):
                    pixel = image.getpixel((x, y))
                    r, g, b, a = (pixel if len(pixel) == 4 else (*pixel, 255))
                    if x not in data_dict:
                        data_dict[x] = ([r], [g], [b], [a])
                    else:
                        data_dict[x][0].append(r)
                        data_dict[x][1].append(g)
                        data_dict[x][2].append(b)
                        data_dict[x][3].append(a)
        elif scan_direction == "bottom_to_top":
            for y in range(new_height - 1, -1, -1):
                for x in range(new_width):
                    pixel = image.getpixel((x, y))
                    r, g, b, a = (pixel if len(pixel) == 4 else (*pixel, 255))
                    if y not in data_dict:
                        data_dict[y] = ([r], [g], [b], [a])
                    else:
                        data_dict[y][0].append(r)
                        data_dict[y][1].append(g)
                        data_dict[y][2].append(b)
                        data_dict[y][3].append(a)
        elif scan_direction == "top_to_bottom":
            for y in range(new_height):
                for x in range(new_width):
                    pixel = image.getpixel((x, y))
                    r, g, b, a = (pixel if len(pixel) == 4 else (*pixel, 255))
                    if y not in data_dict:
                        data_dict[y] = ([r], [g], [b], [a])
                    else:
                        data_dict[y][0].append(r)
                        data_dict[y][1].append(g)
                        data_dict[y][2].append(b)
                        data_dict[y][3].append(a)

        with open(output_file, 'w') as result_file:
            for key, values in data_dict.items():
                avg_r = sum(values[0]) / len(values[0])
                avg_g = sum(values[1]) / len(values[1])
                avg_b = sum(values[2]) / len(values[2])
                result_file.write(f"{avg_r:.2f} {avg_g:.2f} {avg_b:.2f}\n")

    def execute_program(self):
        img_path = self.image_path_var.get()
        output_path = self.output_path_var.get()
        filename = self.filename_var.get()
        if not img_path or not output_path or not filename:
            messagebox.showwarning("Warning!", "Please enter the image address, output file address, and file name!")
            return

        output_file = f"{output_path}/{filename}.txt"
        try:
            image = Image.open(img_path)
            radius = self.get_radius()
            if self.gaussian_var.get():
                image = image.filter(ImageFilter.GaussianBlur(radius))
            self.save_and_compute_averages(image, output_file)
            self.message_label.config(text=f"Image processing complete! The output file is saved at: {output_file}")
            # messagebox.showinfo("完成", "程序执行完成！")
        except Exception as e:
            messagebox.showerror("Error!", f"Error executing program: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("790x390")
    center_window(root)
    app = ImageBlurApp(root)
    root.mainloop()
