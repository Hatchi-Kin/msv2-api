from typing import Any, Dict, Optional
from pydantic import BaseModel


class ResumeAgentRequest(BaseModel):
    action: str
    playlist_id: int
    track_id: Optional[int] = None
    payload: Dict[str, Any] = {}
