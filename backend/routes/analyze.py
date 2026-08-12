from fastapi import APIRouter, HTTPException
from data_storage.session_store import get_session_store, Session
from services.analyze_passport import analyze_passport
from services.build_travel_history import build_travel_history
from models import PageExtractionResponse, StampRecord, PageExtractionMetadata, UploadedPageInfo, AnalysisResponse
from helpers.create_b64_url import create_base64_url

router = APIRouter(prefix="/api")


@router.post("/sessions/{session_id}/analyze", response_model=AnalysisResponse)
async def analyze(session_id: str):
    session = get_session_store().sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    pages = session.uploaded_pages

    stamps, pages_metadata = analyze_passport(pages)

    session.stamps = stamps
    session.pages_metadata = pages_metadata

    travel_history = build_travel_history(stamps)

    page_response = build_all_page_responses(session)

    return AnalysisResponse(pages=page_response, travel_history=travel_history)


def build_page_extraction_response(
    page_id: str, 
    uploaded_page: UploadedPageInfo,
    page_metadata: PageExtractionMetadata,
    stamps: dict[str, StampRecord]
) -> PageExtractionResponse:
    page_stamps = [stamp for stamp in stamps.values() if stamp.page_id == page_id]

    return PageExtractionResponse(
        page_id=page_id,
        source_filename=uploaded_page.source_filename,
        page_number=uploaded_page.page_number,
        orig_image=create_base64_url(uploaded_page.image),
        processed_image=page_metadata.processed_image,
        image_width=page_metadata.image_width,
        image_height=page_metadata.image_height,
        total_stamps_detected=page_metadata.total_stamps_detected,
        total_stamps_parsed=page_metadata.total_stamps_parsed,
        unreadable_stamps=page_metadata.unreadable_stamps,
        stamps=page_stamps
    )


def build_all_page_responses(session: Session):
    return [
        build_page_extraction_response(
            page_id=page_id,
            uploaded_page=session.uploaded_pages[page_id],
            page_metadata=page_metadata,
            stamps=session.stamps
        )
        for page_id, page_metadata in session.pages_metadata.items()
    ]
