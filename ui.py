import os
import tkinter as tk
from tkinter import filedialog, ttk
from PIL import ImageTk

from image_processor import ImageProcessor
from utils import get_file_format, show_error, show_info, show_success

class ImageCropperUI:
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
        
        # Variables para edición de selección
        self.is_moving = False
        self.is_resizing = False
        self.resize_handle = None
        self.last_x = None
        self.last_y = None
        self.handle_size = 8  # Tamaño de los puntos de control
        self.handle_ids = []  # IDs de los puntos de control
        
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
            self.original_image = ImageProcessor.open_image(file_path)
            self.reset_crop(reload=True)
            
            # Update status
            filename = os.path.basename(file_path)
            self.status_label.config(text=f"Estado: Imagen cargada - {filename}")
            
            # Enable buttons
            self.crop_btn.config(state=tk.NORMAL)
            self.reset_btn.config(state=tk.NORMAL)
            
        except Exception as e:
            show_error("Error", f"No se pudo abrir la imagen: {str(e)}")
    
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
        
        # Resize image to fit canvas
        self.displayed_image, (new_width, new_height) = ImageProcessor.resize_to_fit(
            self.original_image, canvas_width, canvas_height
        )
        
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
        
        # Si ya tenemos una selección, comprobamos si estamos haciendo clic en un punto de control o en la selección
        if self.crop_rectangle and self.rect_id:
            # Comprobar si estamos en un punto de control
            for handle_id in self.handle_ids:
                handle_coords = self.canvas.coords(handle_id)
                if (handle_coords[0] <= event.x <= handle_coords[2] and 
                    handle_coords[1] <= event.y <= handle_coords[3]):
                    self.is_resizing = True
                    self.resize_handle = handle_id
                    self.last_x = event.x
                    self.last_y = event.y
                    return
            
            # Comprobar si estamos dentro de la selección para moverla
            x1, y1, x2, y2 = self.crop_rectangle
            x1 += x
            y1 += y
            x2 += x
            y2 += y
            
            if self.crop_shape == "circular":
                # Para formas circulares, comprobar si estamos dentro del círculo
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                radius = (x2 - x1) / 2
                distance = ((event.x - center_x) ** 2 + (event.y - center_y) ** 2) ** 0.5
                if distance <= radius:
                    self.is_moving = True
                    self.last_x = event.x
                    self.last_y = event.y
                    return
            else:
                # Para formas rectangulares
                if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                    self.is_moving = True
                    self.last_x = event.x
                    self.last_y = event.y
                    return
        
        # Si no estamos editando una selección existente, creamos una nueva
        if x <= event.x <= x + width and y <= event.y <= y + height:
            self.start_x = event.x
            self.start_y = event.y
            
            # Eliminar selección anterior
            self._clear_selection()
            
            # Crear rectángulo inicial
            self.rect_id = self.canvas.create_rectangle(
                self.start_x, self.start_y, self.start_x, self.start_y,
                outline="red", width=2
            )
    
    def on_mouse_move(self, event):
        x, y, width, height = self.image_position
        
        # Caso 1: Estamos redimensionando la selección
        if self.is_resizing and self.resize_handle:
            # Calcular el movimiento
            delta_x = event.x - self.last_x
            delta_y = event.y - self.last_y
            
            # Obtener las coordenadas actuales
            x1, y1, x2, y2 = self.crop_rectangle
            x1_canvas = x1 + x
            y1_canvas = y1 + y
            x2_canvas = x2 + x
            y2_canvas = y2 + y
            
            # Identificar qué esquina estamos moviendo
            handle_coords = self.canvas.coords(self.resize_handle)
            handle_center_x = (handle_coords[0] + handle_coords[2]) / 2
            handle_center_y = (handle_coords[1] + handle_coords[3]) / 2
            
            # Esquina superior izquierda
            if abs(handle_center_x - x1_canvas) < 10 and abs(handle_center_y - y1_canvas) < 10:
                x1 += delta_x
                y1 += delta_y
                if self.fixed_ratio:
                    # Mantener proporción
                    aspect_diff = abs((x2 - x1) / (y2 - y1) - self.fixed_ratio)
                    if aspect_diff > 0.01:
                        if (x2 - x1) / (y2 - y1) > self.fixed_ratio:
                            y1 = y2 - (x2 - x1) / self.fixed_ratio
                        else:
                            x1 = x2 - (y2 - y1) * self.fixed_ratio
            
            # Esquina superior derecha
            elif abs(handle_center_x - x2_canvas) < 10 and abs(handle_center_y - y1_canvas) < 10:
                x2 += delta_x
                y1 += delta_y
                if self.fixed_ratio:
                    if (x2 - x1) / (y2 - y1) > self.fixed_ratio:
                        y1 = y2 - (x2 - x1) / self.fixed_ratio
                    else:
                        x2 = x1 + (y2 - y1) * self.fixed_ratio
            
            # Esquina inferior izquierda
            elif abs(handle_center_x - x1_canvas) < 10 and abs(handle_center_y - y2_canvas) < 10:
                x1 += delta_x
                y2 += delta_y
                if self.fixed_ratio:
                    if (x2 - x1) / (y2 - y1) > self.fixed_ratio:
                        y2 = y1 + (x2 - x1) / self.fixed_ratio
                    else:
                        x1 = x2 - (y2 - y1) * self.fixed_ratio
            
            # Esquina inferior derecha
            elif abs(handle_center_x - x2_canvas) < 10 and abs(handle_center_y - y2_canvas) < 10:
                x2 += delta_x
                y2 += delta_y
                if self.fixed_ratio:
                    if (x2 - x1) / (y2 - y1) > self.fixed_ratio:
                        y2 = y1 + (x2 - x1) / self.fixed_ratio
                    else:
                        x2 = x1 + (y2 - y1) * self.fixed_ratio
            
            # Asegurar que estamos dentro de los límites de la imagen
            x1 = max(0, min(x1, width))
            y1 = max(0, min(y1, height))
            x2 = max(0, min(x2, width))
            y2 = max(0, min(y2, height))
            
            # Actualizar la selección
            self.crop_rectangle = (x1, y1, x2, y2)
            self._update_selection_display()
            
            self.last_x = event.x
            self.last_y = event.y
            return
        
        # Caso 2: Estamos moviendo la selección
        elif self.is_moving:
            # Calcular el movimiento
            delta_x = event.x - self.last_x
            delta_y = event.y - self.last_y
            
            # Obtener las coordenadas actuales
            x1, y1, x2, y2 = self.crop_rectangle
            
            # Mover la selección
            x1 += delta_x
            y1 += delta_y
            x2 += delta_x
            y2 += delta_y
            
            # Asegurar que estamos dentro de los límites de la imagen
            if x1 < 0:
                x2 -= x1
                x1 = 0
            if y1 < 0:
                y2 -= y1
                y1 = 0
            if x2 > width:
                x1 -= (x2 - width)
                x2 = width
            if y2 > height:
                y1 -= (y2 - height)
                y2 = height
            
            # Actualizar la selección
            self.crop_rectangle = (x1, y1, x2, y2)
            self._update_selection_display()
            
            self.last_x = event.x
            self.last_y = event.y
            return
        
        # Caso 3: Estamos creando una nueva selección
        if not self.start_x or not self.start_y or not self.rect_id:
            return
        
        # Update rectangle as mouse moves
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
        # Si estábamos moviendo o redimensionando, terminamos la operación
        if self.is_moving or self.is_resizing:
            self.is_moving = False
            self.is_resizing = False
            self.resize_handle = None
            return
        
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
            
            # Ordenar coordenadas
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1
                
            self.crop_rectangle = (x1, y1, x2, y2)
            self._update_selection_display()
            self.crop_btn.config(state=tk.NORMAL)
        else:
            # If it's just a click or very small rectangle, clear it
            self._clear_selection()
    
    def _clear_selection(self):
        """Limpia la selección actual y los puntos de control"""
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        
        for handle_id in self.handle_ids:
            self.canvas.delete(handle_id)
        
        self.rect_id = None
        self.handle_ids = []
        self.crop_rectangle = None
        self.start_x = None
        self.start_y = None
    
    def _update_selection_display(self):
        """Actualiza la visualización de la selección y los puntos de control"""
        x, y, width, height = self.image_position
        x1, y1, x2, y2 = self.crop_rectangle
        
        # Asegurar que las coordenadas están ordenadas
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        
        # Actualizar el rectángulo o círculo de selección
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        
        if self.crop_shape == "circular":
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            radius = max(abs(x2 - x1), abs(y2 - y1)) / 2
            
            self.rect_id = self.canvas.create_oval(
                center_x - radius + x, center_y - radius + y,
                center_x + radius + x, center_y + radius + y,
                outline="red", width=2
            )
        else:
            self.rect_id = self.canvas.create_rectangle(
                x1 + x, y1 + y, x2 + x, y2 + y,
                outline="red", width=2
            )
        
        # Eliminar puntos de control anteriores
        for handle_id in self.handle_ids:
            self.canvas.delete(handle_id)
        
        self.handle_ids = []
        
        # Crear nuevos puntos de control en las esquinas
        handle_positions = [
            (x1, y1),  # Superior izquierda
            (x2, y1),  # Superior derecha
            (x1, y2),  # Inferior izquierda
            (x2, y2)   # Inferior derecha
        ]
        
        for hx, hy in handle_positions:
            handle = self.canvas.create_rectangle(
                hx + x - self.handle_size/2, hy + y - self.handle_size/2,
                hx + x + self.handle_size/2, hy + y + self.handle_size/2,
                fill="white", outline="blue", width=1
            )
            self.handle_ids.append(handle)
    
    def crop_image(self):
        if not self.crop_rectangle or not self.displayed_image:
            show_info("Información", "Por favor, seleccione un área para recortar primero.")
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
        
        # Crop the image using the processor
        self.cropped_image = ImageProcessor.crop_image(
            self.original_image, 
            (orig_x1, orig_y1, orig_x2, orig_y2), 
            self.crop_shape
        )
        
        # Display cropped image
        self.original_image = self.cropped_image.copy()
        self.reset_crop(reload=True)
        
        # Enable save button
        self.save_btn.config(state=tk.NORMAL)
        
        # Update status
        self.status_label.config(text="Estado: Imagen recortada")
    
    def save_image(self):
        if not hasattr(self, 'cropped_image'):
            show_info("Información", "No hay imagen recortada para guardar.")
            return
        
        # Get file format information
        file_format, original_ext = get_file_format(self.image_path)
        
        # Open save file dialog
        save_path = filedialog.asksaveasfilename(
            title="Guardar Imagen Recortada",
            defaultextension=original_ext,
            filetypes=[(f"Imagen {original_ext}", f"*{original_ext}"), ("Todos los archivos", "*.*")]
        )
        
        if not save_path:
            return
        
        try:
            # Save the image using the processor
            ImageProcessor.save_image(self.cropped_image, save_path, file_format)
            
            # Update status
            self.status_label.config(text=f"Estado: Imagen guardada en {os.path.basename(save_path)}")
            show_success("Éxito", "Imagen guardada correctamente.")
            
        except Exception as e:
            show_error("Error", f"No se pudo guardar la imagen: {str(e)}")
    
    def reset_crop(self, reload=False):
        # Clear canvas and reset crop variables
        self._clear_selection()
        
        if reload and self.original_image:
            self.display_image()
        
        # Update status if not reloading
        if not reload and self.image_path:
            self.status_label.config(text=f"Estado: Recorte reiniciado")
            self.crop_btn.config(state=tk.DISABLED)