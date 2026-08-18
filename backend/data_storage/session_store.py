from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, Dict

from models import UploadedPageInfo, PageExtractionMetadata, TravelHistoryResponse, StampRecord


@dataclass
class Session:
    uploaded_pages: Dict[str, UploadedPageInfo] = field(default_factory=dict)
    pages_metadata: Dict[str, PageExtractionMetadata] = field(default_factory=dict)
    stamps: Dict[str, StampRecord] = field(default_factory=dict)
    travel_history_reconstruction: Optional[TravelHistoryResponse] = None


@dataclass
class SessionStore:
    sessions: Dict[str, Session] = field(default_factory=dict)


session_store = SessionStore()

def get_session_store() -> SessionStore:
    return session_store
