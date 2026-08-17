import numpy as np
import cv2
from PIL import Image
import io
import base64

def create_base64_url(img_array: np.ndarray, format: str = "png") -> str:
    if img_array.dtype != np.uint8:
        img_array = np.clip(img_array, 0, 255).astype(np.uint8)

    if img_array.shape[-1] == 4:
        mode = "RGBA"
    else:
        mode = "RGB"
        
    img = Image.fromarray(img_array, mode=mode)

    buffer = io.BytesIO()
    img.save(buffer, format=format)
    buffer.seek(0)

    b64_str = base64.b64encode(buffer.read()).decode("utf-8")

    mime = f"image/{format.lower()}"
    return f"data:{mime};base64,{b64_str}"