from fastapi import APIRouter, UploadFile, Depends, Form, HTTPException
from concurrent.futures import ProcessPoolExecutor
import fitz
import os
import tempfile
import numpy as np
import cv2

from services.pdf_conversion import render_pdf_page_thumbnail, render_pdf_page_full_res
from data_storage.session_store import get_session_store, SessionStore
from models import UploadedPageInfo

router = APIRouter(prefix="/api")

@router.get("/")
def test():
    return {"status": "ok"}

@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile, session_id: str = Form(...), store: SessionStore = Depends(get_session_store)):
    frontend_pages = []

    pdf_bytes = await file.read()

    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        doc_page_count = doc.page_count

    with tempfile.NamedTemporaryFile(suffix="pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        pdf_path = tmp.name

    if doc_page_count <= 5:
        for page_num in range(doc_page_count):
            _, data_url = render_pdf_page_thumbnail(pdf_path, page_num)
            frontend_pages.append({"pageNumber": page_num, "imgUrl": data_url})

            _, full_res_img = render_pdf_page_full_res(pdf_path, page_num)
            page_info = UploadedPageInfo(
                source_filename=file.filename,
                page_number=page_num,
                image=full_res_img
            )

            store.sessions[session_id].append(page_info)

    else:
        with ProcessPoolExecutor(max_workers=min(doc_page_count, os.cpu_count())) as executor:
            frontend_results = list(
                executor.map(
                    render_pdf_page_thumbnail, 
                    [pdf_path] * doc_page_count, 
                    [i for i in range(doc_page_count)]
                )
            )
            frontend_pages = [
                {"pageNumber": page_num, "imgUrl": data_url} for page_num, data_url in frontend_results
            ]

            backend_results = list(
                executor.map(
                    render_pdf_page_full_res,
                    [pdf_path] * doc_page_count,
                    [i for i in range(doc_page_count)]
                )
            )
            for page_num, full_res_img in backend_results:
                page_info = UploadedPageInfo(
                    source_filename=file.filename,
                    page_number=page_num,
                    image=full_res_img
                )

                store.sessions[session_id].append(page_info)

    try:
        os.remove(pdf_path)
    except FileNotFoundError:
        print(f"Temp file {pdf_path} already removed or not found")

    return {"pages": frontend_pages}


@router.post("/upload-image")
async def upload_image(file: UploadFile, session_id: str = Form(...), store: SessionStore = Depends(get_session_store)):
    img_bytes = await file.read()
    arr = np.frombuffer(img_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(status_code=400, detail="Could not decode image.")

    page_info = UploadedPageInfo(
                    source_filename=file.filename,
                    page_number=1,
                    image=img
                )

    store.sessions[session_id].append(page_info)

    return {"status": "successful upload"}
