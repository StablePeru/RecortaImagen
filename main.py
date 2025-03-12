import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageDraw
import math

class ImageCropperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Recorta Imagen")
        self.root.geometry("800x600")
        
        # Variables
        self.image_path = None
        self.original_image = None
        self.displayed_image = None
        self.image_tk = None
        self.crop_rectangle = None
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.aspect_ratio = None
        self.crop_shape = "rectangular"  # Default shape
        self.fixed_ratio = None  # Default no fixed ratio
        
        # Create UI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Top frame for buttons
        top_frame = tk.Frame(self.root)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        # Buttons
        self.open_btn = tk.Button(top_frame, text="Abrir Imagen", command=self.open_image)
        self.open_btn.pack(side=tk.LEFT, padx=5)
        
        self.crop_btn = tk.Button(top_frame, text="Recortar", command=self.crop_image, state=tk.DISABLED)
        self.crop_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = tk.Button(top_frame, text="Guardar", command=self.save_image, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        self.reset_btn = tk.Button(top_frame, text="Reiniciar", command=self.reset_crop, state=tk.DISABLED)
        self.reset_btn.pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = tk.Label(top_frame, text="Estado: Listo para abrir imagen")
        self.status_label.pack(side=tk.RIGHT, padx=5)
        
        # Options frame
        options_frame = tk.Frame(self.root)
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Shape selection
        shape_label = tk.Label(options_frame, text="Forma de recorte:")
        shape_label.pack(side=tk.LEFT, padx=5)
        
        self.shape_var = tk.StringVar(value="rectangular")
        shape_combo = ttk.Combobox(options_frame, textvariable=self.shape_var, 
                                  values=["rectangular", "cuadrado", "circular"],
                                  width=10, state="readonly")
        shape_combo.pack(side=tk.LEFT, padx=5)
        shape_combo.bind("<<ComboboxSelected>>", self.on_shape_change)
        
        # Aspect ratio selection
        ratio_label = tk.Label(options_frame, text="Proporción:")
        ratio_label.pack(side=tk.LEFT, padx=5)
        
        self.ratio_var = tk.StringVar(value="libre")
        ratio_options = ["libre", "1:1", "4:3", "16:9", "3:2", "2:3", "9:16"]
        ratio_combo = ttk.Combobox(options_frame, textvariable=self.ratio_var, 
                                  values=ratio_options, width=10, state="readonly")
        ratio_combo.pack(side=tk.LEFT, padx=5)
        ratio_combo.bind("<<ComboboxSelected>>", self.on_ratio_change)
        
        # Canvas for image display
        self.canvas_frame = tk.Frame(self.root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="#f0f0f0", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse events for cropping
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        # Information label
        self.info_label = tk.Label(self.root, text="Haga clic y arrastre para seleccionar el área de recorte")
        self.info_label.pack(side=tk.BOTTOM, pady=5)
    
    def on_shape_change(self, event=None):
        shape = self.shape_var.get()
        self.crop_shape = shape
        
        # If shape is square or circular, force 1:1 aspect ratio
        if shape in ["cuadrado", "circular"]:
            self.ratio_var.set("1:1")
            self.on_ratio_change()
        
        # Reset crop if we have an image
        if self.original_image:
            self.reset_crop()
    
    def on_ratio_change(self, event=None):
        ratio_str = self.ratio_var.get()
        
        if ratio_str == "libre":
            self.fixed_ratio = None
        else:
            # Parse ratio like "16:9" to a float
            try:
                w, h = map(int, ratio_str.split(':'))
                self.fixed_ratio = w / h
            except:
                self.fixed_ratio = None
        
        # Reset crop if we have an image
        if self.original_image:
            self.reset_crop()
    
    def open_image(self):
        # Open file dialog to select an image
        file_path = filedialog.askopenfilename(
            title="Seleccionar Imagen",
            filetypes=[
                ("Imágenes", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            # Open and display the image
            self.image_path = file_path
            self.original_image = Image.open(file_path)
            self.reset_crop(reload=True)
            
            # Update status
            filename = os.path.basename(file_path)
            self.status_label.config(text=f"Estado: Imagen cargada - {filename}")
            
            # Enable buttons
            self.crop_btn.config(state=tk.NORMAL)
            self.reset_btn.config(state=tk.NORMAL)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la imagen: {str(e)}")
    
    def display_image(self):
        # Clear canvas
        self.canvas.delete("all")
        
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            # Canvas not ready yet, schedule this function to run later
            self.root.after(100, self.display_image)
            return
        
        # Resize image to fit canvas while maintaining aspect ratio
        img_width, img_height = self.original_image.size
        self.aspect_ratio = img_width / img_height
        
        if img_width > img_height:
            new_width = min(img_width, canvas_width)
            new_height = int(new_width / self.aspect_ratio)
            if new_height > canvas_height:
                new_height = canvas_height
                new_width = int(new_height * self.aspect_ratio)
        else:
            new_height = min(img_height, canvas_height)
            new_width = int(new_height * self.aspect_ratio)
            if new_width > canvas_width:
                new_width = canvas_width
                new_height = int(new_width / self.aspect_ratio)
        
        # Resize image for display
        self.displayed_image = self.original_image.copy()
        self.displayed_image.thumbnail((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage for canvas
        self.image_tk = ImageTk.PhotoImage(self.displayed_image)
        
        # Calculate position to center image
        x_position = (canvas_width - new_width) // 2
        y_position = (canvas_height - new_height) // 2
        
        # Display image on canvas
        self.canvas.create_image(x_position, y_position, anchor=tk.NW, image=self.image_tk)
        
        # Store image position for coordinate calculations
        self.image_position = (x_position, y_position, new_width, new_height)
    
    def on_mouse_down(self, event):
        if not self.displayed_image:
            return
        
        # Check if click is within image bounds
        x, y, width, height = self.image_position
        if x <= event.x <= x + width and y <= event.y <= y + height:
            self.start_x = event.x
            self.start_y = event.y
            
            # Create initial rectangle
            if self.rect_id:
                self.canvas.delete(self.rect_id)
            
            self.rect_id = self.canvas.create_rectangle(
                self.start_x, self.start_y, self.start_x, self.start_y,
                outline="red", width=2
            )
    
    def on_mouse_move(self, event):
        if not self.start_x or not self.start_y or not self.rect_id:
            return
        
        # Update rectangle as mouse moves
        x, y, width, height = self.image_position
        current_x = max(x, min(event.x, x + width))
        current_y = max(y, min(event.y, y + height))
        
        # Apply fixed aspect ratio if needed
        if self.fixed_ratio:
            # Calculate width and height of the selection
            w = abs(current_x - self.start_x)
            h = abs(current_y - self.start_y)
            
            # Determine direction of drag
            drag_right = current_x >= self.start_x
            drag_down = current_y >= self.start_y
            
            # Adjust width or height to maintain aspect ratio
            if w / h > self.fixed_ratio:
                # Width is too large, adjust it
                w = h * self.fixed_ratio
            else:
                # Height is too large, adjust it
                h = w / self.fixed_ratio
            
            # Apply the adjusted dimensions
            if drag_right:
                current_x = self.start_x + w
            else:
                current_x = self.start_x - w
                
            if drag_down:
                current_y = self.start_y + h
            else:
                current_y = self.start_y - h
            
            # Ensure we stay within image bounds
            current_x = max(x, min(current_x, x + width))
            current_y = max(y, min(current_y, y + height))
        
        # Update the rectangle
        self.canvas.delete(self.rect_id)
        
        if self.crop_shape == "circular":
            # For circular shape, draw a circle
            # Calculate radius based on the larger dimension
            radius = max(abs(current_x - self.start_x), abs(current_y - self.start_y)) / 2
            center_x = (self.start_x + current_x) / 2
            center_y = (self.start_y + current_y) / 2
            
            self.rect_id = self.canvas.create_oval(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                outline="red", width=2
            )
        else:
            # For rectangular or square, draw a rectangle
            self.rect_id = self.canvas.create_rectangle(
                self.start_x, self.start_y, current_x, current_y,
                outline="red", width=2
            )
    
    def on_mouse_up(self, event):
        if not self.start_x or not self.start_y or not self.rect_id:
            return
        
        # Finalize rectangle
        x, y, width, height = self.image_position
        end_x = max(x, min(event.x, x + width))
        end_y = max(y, min(event.y, y + height))
        
        # Apply fixed aspect ratio if needed
        if self.fixed_ratio:
            # Calculate width and height of the selection
            w = abs(end_x - self.start_x)
            h = abs(end_y - self.start_y)
            
            # Determine direction of drag
            drag_right = end_x >= self.start_x
            drag_down = end_y >= self.start_y
            
            # Adjust width or height to maintain aspect ratio
            if w / h > self.fixed_ratio:
                # Width is too large, adjust it
                w = h * self.fixed_ratio
            else:
                # Height is too large, adjust it
                h = w / self.fixed_ratio
            
            # Apply the adjusted dimensions
            if drag_right:
                end_x = self.start_x + w
            else:
                end_x = self.start_x - w
                
            if drag_down:
                end_y = self.start_y + h
            else:
                end_y = self.start_y - h
            
            # Ensure we stay within image bounds
            end_x = max(x, min(end_x, x + width))
            end_y = max(y, min(end_y, y + height))
        
        # Ensure we have a valid rectangle (not just a click)
        if abs(end_x - self.start_x) > 10 and abs(end_y - self.start_y) > 10:
            # Store crop coordinates relative to displayed image
            x1 = max(0, self.start_x - x)
            y1 = max(0, self.start_y - y)
            x2 = max(0, end_x - x)
            y2 = max(0, end_y - y)
            
            # For circular shape, ensure it's a perfect circle
            if self.crop_shape == "circular":
                # Calculate center and radius
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                radius = max(abs(x2 - x1), abs(y2 - y1)) / 2
                
                # Update coordinates to be a perfect circle
                x1 = center_x - radius
                y1 = center_y - radius
                x2 = center_x + radius
                y2 = center_y + radius
                
                # Update the visual representation
                self.canvas.delete(self.rect_id)
                self.rect_id = self.canvas.create_oval(
                    x1 + x, y1 + y, x2 + x, y2 + y,
                    outline="red", width=2
                )
            
            self.crop_rectangle = (x1, y1, x2, y2)
            self.crop_btn.config(state=tk.NORMAL)
        else:
            # If it's just a click or very small rectangle, clear it
            self.canvas.delete(self.rect_id)
            self.rect_id = None
            self.crop_rectangle = None
    
    def crop_image(self):
        if not self.crop_rectangle or not self.displayed_image:
            messagebox.showinfo("Información", "Por favor, seleccione un área para recortar primero.")
            return
        
        # Get crop coordinates relative to displayed image
        x1, y1, x2, y2 = self.crop_rectangle
        
        # Sort coordinates (in case of drawing from bottom-right to top-left)
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        
        # Scale coordinates to original image size
        orig_width, orig_height = self.original_image.size
        disp_width, disp_height = self.displayed_image.size
        
        scale_x = orig_width / disp_width
        scale_y = orig_height / disp_height
        
        orig_x1 = int(x1 * scale_x)
        orig_y1 = int(y1 * scale_y)
        orig_x2 = int(x2 * scale_x)
        orig_y2 = int(y2 * scale_y)
        
        if self.crop_shape == "circular":
            # For circular crop, we need to create a circular mask
            # First, crop the rectangular region
            temp_crop = self.original_image.crop((orig_x1, orig_y1, orig_x2, orig_y2))
            
            # Create a mask with a white circle on black background
            mask = Image.new('L', temp_crop.size, 0)
            draw = ImageDraw.Draw(mask)
            width, height = temp_crop.size
            draw.ellipse((0, 0, width, height), fill=255)
            
            # Create a transparent image for the result
            self.cropped_image = Image.new('RGBA', temp_crop.size, (0, 0, 0, 0))
            
            # Convert temp_crop to RGBA if it's not already
            if temp_crop.mode != 'RGBA':
                temp_crop = temp_crop.convert('RGBA')
            
            # Paste the cropped image using the mask
            self.cropped_image.paste(temp_crop, (0, 0), mask)
        else:
            # For rectangular or square, just crop normally
            self.cropped_image = self.original_image.crop((orig_x1, orig_y1, orig_x2, orig_y2))
        
        # Display cropped image
        self.original_image = self.cropped_image.copy()
        self.reset_crop(reload=True)
        
        # Enable save button
        self.save_btn.config(state=tk.NORMAL)
        
        # Update status
        self.status_label.config(text="Estado: Imagen recortada")
    
    def save_image(self):
        if not hasattr(self, 'cropped_image'):
            messagebox.showinfo("Información", "No hay imagen recortada para guardar.")
            return
        
        # Get original file extension
        original_ext = os.path.splitext(self.image_path)[1].lower()
        
        # Determine file format for saving
        file_format = original_ext[1:].upper()  # Remove dot and convert to uppercase
        if file_format == 'JPG':
            file_format = 'JPEG'
        
        # Open save file dialog
        save_path = filedialog.asksaveasfilename(
            title="Guardar Imagen Recortada",
            defaultextension=original_ext,
            filetypes=[(f"Imagen {original_ext}", f"*{original_ext}"), ("Todos los archivos", "*.*")]
        )
        
        if not save_path:
            return
        
        try:
            # Save the cropped image in the original format
            if file_format == 'JPEG':
                self.cropped_image.save(save_path, format=file_format, quality=95)
            else:
                self.cropped_image.save(save_path, format=file_format)
            
            # Update status
            self.status_label.config(text=f"Estado: Imagen guardada en {os.path.basename(save_path)}")
            messagebox.showinfo("Éxito", "Imagen guardada correctamente.")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la imagen: {str(e)}")
    
    def reset_crop(self, reload=False):
        # Clear canvas and reset crop variables
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        
        self.rect_id = None
        self.crop_rectangle = None
        self.start_x = None
        self.start_y = None
        
        if reload and self.original_image:
            self.display_image()
        
        # Update status if not reloading
        if not reload and self.image_path:
            self.status_label.config(text=f"Estado: Recorte reiniciado")
            self.crop_btn.config(state=tk.DISABLED)

def main():
    root = tk.Tk()
    app = ImageCropperApp(root)
    root.update()
    # Remove the initial display_image call since no image is loaded yet
    root.mainloop()

if __name__ == "__main__":
    main()