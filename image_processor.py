from PIL import Image, ImageDraw

class ImageProcessor:
    @staticmethod
    def resize_to_fit(image, target_width, target_height):
        """Redimensiona una imagen para que quepa en las dimensiones objetivo manteniendo la proporción."""
        img_width, img_height = image.size
        aspect_ratio = img_width / img_height
        
        if img_width > img_height:
            new_width = min(img_width, target_width)
            new_height = int(new_width / aspect_ratio)
            if new_height > target_height:
                new_height = target_height
                new_width = int(new_height * aspect_ratio)
        else:
            new_height = min(img_height, target_height)
            new_width = int(new_height * aspect_ratio)
            if new_width > target_width:
                new_width = target_width
                new_height = int(new_width / aspect_ratio)
        
        resized_image = image.copy()
        resized_image.thumbnail((new_width, new_height), Image.Resampling.LANCZOS)
        return resized_image, (new_width, new_height)
    
    @staticmethod
    def crop_image(image, crop_coords, crop_shape="rectangular"):
        """Recorta una imagen según las coordenadas y forma especificadas."""
        x1, y1, x2, y2 = crop_coords
        
        # Sort coordinates
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        
        if crop_shape == "circular":
            # For circular crop, create a circular mask
            temp_crop = image.crop((x1, y1, x2, y2))
            
            # Create a mask with a white circle on black background
            mask = Image.new('L', temp_crop.size, 0)
            draw = ImageDraw.Draw(mask)
            width, height = temp_crop.size
            draw.ellipse((0, 0, width, height), fill=255)
            
            # Create a transparent image for the result
            result = Image.new('RGBA', temp_crop.size, (0, 0, 0, 0))
            
            # Convert temp_crop to RGBA if it's not already
            if temp_crop.mode != 'RGBA':
                temp_crop = temp_crop.convert('RGBA')
            
            # Paste the cropped image using the mask
            result.paste(temp_crop, (0, 0), mask)
        else:
            # For rectangular or square, just crop normally
            result = image.crop((x1, y1, x2, y2))
        
        return result
    
    @staticmethod
    def save_image(image, save_path, file_format, quality=95):
        """Guarda una imagen en el formato especificado."""
        if file_format == 'JPEG':
            # JPEG doesn't support transparency, convert to RGB if needed
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            image.save(save_path, format=file_format, quality=quality)
        else:
            image.save(save_path, format=file_format)
    
    @staticmethod
    def open_image(file_path):
        """Abre una imagen desde un archivo."""
        return Image.open(file_path)