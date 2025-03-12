import os
from tkinter import messagebox

def get_file_format(file_path):
    """Obtiene el formato de archivo a partir de la extensión."""
    original_ext = os.path.splitext(file_path)[1].lower()
    file_format = original_ext[1:].upper()  # Remove dot and convert to uppercase
    if file_format == 'JPG':
        file_format = 'JPEG'
    return file_format, original_ext

def show_error(title, message):
    """Muestra un mensaje de error."""
    messagebox.showerror(title, message)

def show_info(title, message):
    """Muestra un mensaje informativo."""
    messagebox.showinfo(title, message)

def show_success(title, message):
    """Muestra un mensaje de éxito."""
    messagebox.showinfo(title, message)