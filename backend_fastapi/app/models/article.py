from pydantic import BaseModel
from typing import Optional

class Article(BaseModel):
    title: str
    url: str
    summary: str
    section: str
    date: str
    imageUrl: Optional[str] = None