from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class NoteCreate(BaseModel):
    topic: str = Field(..., min_length=1, max_length=100, description="The topic of the note")
    content: str = Field(..., min_length=1, max_length=5000, description="The content of the note")
    author: Optional[str] = Field("Anonymous", max_length=50, description="The author's nickname")

class NoteUpdate(BaseModel):
    topic: Optional[str] = Field(None, min_length=1, max_length=100)
    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    author: Optional[str] = Field(None, max_length=50)

class NoteResponse(BaseModel):
    id: int
    topic: str
    content: str
    author: str
    created_at: datetime
    votes: int
    pinned: bool = False

    model_config = ConfigDict(from_attributes=True)