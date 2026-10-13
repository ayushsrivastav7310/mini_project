import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image

def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Validate file extension against permitted set."""
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in allowed_extensions

def sanitize_and_save_image(file_obj, upload_folder: str, allowed_extensions: set) -> str:
    """Validate image file integrity and save with a safe unique filename."""
    if not file_obj or file_obj.filename == "":
        raise ValueError("No file provided for upload.")

    if not allowed_file(file_obj.filename, allowed_extensions):
        raise ValueError(f"Unsupported file format. Permitted types: {', '.join(allowed_extensions)}")

    original_filename = secure_filename(file_obj.filename)
    extension = original_filename.rsplit(".", 1)[1].lower() if "." in original_filename else "jpg"
    safe_name = f"bmw_scan_{uuid.uuid4().hex[:12]}.{extension}"
    
    os.makedirs(upload_folder, exist_ok=True)
    destination_path = os.path.join(upload_folder, safe_name)
    
    # Save file
    file_obj.save(destination_path)
    
    # Verify file is a valid image using PIL
    try:
        with Image.open(destination_path) as img:
            img.verify()
    except Exception as e:
        if os.path.exists(destination_path):
            os.remove(destination_path)
        raise ValueError(f"Corrupted or invalid image file: {str(e)}")
        
    return safe_name

def validate_quantity(quantity_str: str) -> float:
    """Validate and convert waste weight in kilograms."""
    try:
        qty = float(quantity_str)
        if qty <= 0:
            raise ValueError("Waste quantity must be greater than 0 kg.")
        if qty > 5000:
            raise ValueError("Waste quantity exceeds single-entry safety limit (5000 kg).")
        return round(qty, 2)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid quantity: {str(e)}")
