from pydantic import BaseModel
from typing import Dict, List, Optional
from app.models.article import Article

class DayArchive(BaseModel):
    date: str
    sections: Dict[str, List[Article]]
    cached_at: Optional[str] = None