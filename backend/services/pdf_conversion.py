import fitz
import base64
import numpy as np
import cv2


def render_pdf_page_thumbnail(pdf_path: str, page_num: int):
    """Render a 96 dpi image thumbnail to show in the frontend"""
    with fitz.open(pdf_path) as doc:
        page = doc[page_num]
        pix = page.get_pixmap(dpi=96)
        jpeg_bytes = pix.tobytes("jpeg")
        base64_string = base64.b64encode(jpeg_bytes).decode("utf-8")
        data_url = f"data:image/jpeg;base64,{base64_string}"

    return (page_num, data_url)


def render_pdf_page_full_res(pdf_path: str, page_num: int):
    """Create a 300 dpi image for processing in the backend"""
    with fitz.open(pdf_path) as doc:
        page = doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
        img = np.frombuffer(
            pix.samples, 
            dtype=np.uint8
        ).reshape(pix.h, pix.w, pix.n)
        if pix.n == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        elif pix.n == 1:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    return (page_num, img)
