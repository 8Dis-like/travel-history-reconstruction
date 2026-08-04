from fastapi import APIRouter, Form
from data_storage.session_store import get_session_store, SessionStore
from services.analyze_passport import analyze_passport
from services.build_travel_history import build_travel_history
from models import PageExtractionResponse, TravelHistoryResponse

router = APIRouter(prefix="/api")

@router.post("/analyze")
async def analyze(session_id: str = Form(...)):
    pages = get_session_store().sessions[session_id]

    page_response: list[PageExtractionResponse] = analyze_passport(pages)
    stays = build_travel_history([])

    return {"pages": page_response, "stays": stays}
