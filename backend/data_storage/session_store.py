from collections import defaultdict
from dataclasses import dataclass, field
import numpy as np

from models import UploadedPageInfo

@dataclass
class SessionStore:
    sessions: dict[str, list[UploadedPageInfo]] = field(default_factory=lambda: defaultdict(list))

session_store = SessionStore()

def get_session_store() -> SessionStore:
    return session_store
