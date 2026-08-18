from fastapi import APIRouter, UploadFile, Depends, Form, HTTPException
from concurrent.futures import ProcessPoolExecutor
import fitz
import os
import tempfile
import numpy as np
from PIL import Image
from io import BytesIO
import uuid
from typing import List

from services.pdf_conversion import render_pdf_page_thumbnail, render_pdf_page_full_res
from data_storage.session_store import get_session_store, SessionStore, Session
from models import UploadedPageInfo, UploadResponse

router = APIRouter(prefix="/api")

@router.post("/sessions/{session_id}/upload-pdf", response_model=List[UploadResponse])
async def upload_pdf(file: UploadFile, session_id: str, store: SessionStore = Depends(get_session_store)):
    if session_id not in store.sessions.keys():
        store.sessions[session_id] = Session()

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

            _, full_res_img = render_pdf_page_full_res(pdf_path, page_num)
            page_id = str(uuid.uuid4())

            page_info = UploadedPageInfo(
                page_id=page_id,
                source_filename=file.filename,
                page_number=page_num,
                image=full_res_img
            )

            upload_response = UploadResponse(
                page_id=page_id,
                source_filename=f"{file.filename}_pg{page_num + 1}",
                image_src=data_url
            )

            frontend_pages.append(upload_response)

            store.sessions[session_id].uploaded_pages[page_id] = page_info

    else:
        with ProcessPoolExecutor(max_workers=min(doc_page_count, os.cpu_count())) as executor:
            frontend_results = list(
                executor.map(
                    render_pdf_page_thumbnail, 
                    [pdf_path] * doc_page_count, 
                    [i for i in range(doc_page_count)]
                )
            )

            backend_results = list(
                executor.map(
                    render_pdf_page_full_res,
                    [pdf_path] * doc_page_count,
                    [i for i in range(doc_page_count)]
                )
            )

            page_ids = [str(uuid.uuid4()) for _ in range(doc_page_count)]

            for page_num, (_, data_url) in enumerate(frontend_results):
                page_id = page_ids[page_num]
                frontend_pages.append(
                    UploadResponse(
                        page_id=page_id,
                        source_filename=f"{file.filename}_pg{page_num + 1}",
                        image_src=data_url
                    )
                )

            for page_num, (_, full_res_img) in enumerate(backend_results):
                page_id = page_ids[page_num]

                store.sessions[session_id].uploaded_pages[page_id] = UploadedPageInfo(
                    page_id=page_id,
                    source_filename=file.filename,
                    page_number=page_num,
                    image=full_res_img
                )

    try:
        os.remove(pdf_path)
    except FileNotFoundError:
        print(f"Temp file {pdf_path} already removed or not found")

    return frontend_pages


@router.post("/sessions/{session_id}/upload-image")
async def upload_image(file: UploadFile, session_id: str, page_id: str = Form(...), store: SessionStore = Depends(get_session_store)):
    if session_id not in store.sessions.keys():
        store.sessions[session_id] = Session()

    img_bytes = await file.read()

    try:
        img = Image.open(BytesIO(img_bytes)).convert("RGB")
        img = np.array(img)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not decode image.")

    page_info = UploadedPageInfo(
        page_id=page_id,
        source_filename=file.filename,
        page_number=1,
        image=img
    )

    store.sessions[session_id].uploaded_pages[page_id] = page_info

    return {"status": "ok"}


@router.delete("/sessions/{session_id}/delete-page/{page_id}")
async def delete_page(session_id: str, page_id: str):
    session = get_session_store().sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    removed_page = session.uploaded_pages.pop(page_id, None)

    if removed_page is None:
        raise HTTPException(status_code=404, detail="Page does not exist")

    return {"status": "deleted"}