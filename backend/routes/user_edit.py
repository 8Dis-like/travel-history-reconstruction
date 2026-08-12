from fastapi import APIRouter, UploadFile, Depends, Form, HTTPException

from data_storage.session_store import get_session_store
from models import StampFieldUpdate, StampRecord, TravelHistoryResponse
from services.build_travel_history import build_travel_history

router = APIRouter(prefix="/api")

@router.patch("/sessions/{session_id}/stamps/{stamp_id}", response_model=StampRecord)
def update_stamp(session_id: str, stamp_id: str, stamp_field_update: StampFieldUpdate):
    session = get_session_store().sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    stamp = session.stamps.get(stamp_id)
    if stamp is None:
        raise HTTPException(status_code=404, detail="Stamp not found")

    update_data = stamp_field_update.model_dump(exclude_unset=True)
    for property, value in update_data.items():
        setattr(stamp.extracted_fields, property, value)

    stamp.is_user_edited = True
    return stamp


@router.post("/sessions/{session_id}/stamps/{stamp_id}", response_model=StampRecord)
def revert_stamp(session_id: str, stamp_id: str):
    session = get_session_store().sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    stamp = session.stamps.get(stamp_id)
    if stamp is None:
        raise HTTPException(status_code=404, detail="Stamp not found")

    if stamp.original_fields:
        stamp.extracted_fields = stamp.original_fields.model_copy()
        stamp.is_user_edited = False

    return stamp


@router.post("/sessions/{session_id}/rebuild-travel-history", response_model=TravelHistoryResponse)
def rebuild_travel_history(session_id: str):
    session = get_session_store().sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    travel_history = build_travel_history(session.stamps)
    session.travel_history_reconstruction = travel_history

    return travel_history
    

@router.delete("/sessions/{session_id}/delete-stamp/{stamp_id}")
async def delete_stamp(session_id: str, stamp_id: str):
    session = get_session_store().sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    removed_stamp = session.stamps.pop(stamp_id, None)

    if removed_stamp is None:
        raise HTTPException(status_code=404, detail="Stamp does not exist")

    return removed_stamp
