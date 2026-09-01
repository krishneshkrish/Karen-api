from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SessionListItem(BaseModel):
    session_id: str
    started_at: Optional[datetime] = None
    topic: Optional[str] = None
    final_severity: Optional[str] = "low"
    turn_count: Optional[int] = 0
