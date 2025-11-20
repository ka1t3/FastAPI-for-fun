from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class NoteCreate(BaseModel):
    sujet: str = Field(..., min_length=1, description="The topic of the note")
    contenu: str = Field(..., min_length=1, description="The content of the note")
    auteur: Optional[str] = Field("Anonymous", description="The author's nickname")

class NoteUpdate(BaseModel):
    sujet: Optional[str] = Field(None, min_length=1)
    contenu: Optional[str] = Field(None, min_length=1)
    auteur: Optional[str] = None

class NoteResponse(BaseModel):
    id: int
    sujet: str
    contenu: str
    auteur: str
    date_creation: datetime
    votes: int
    pinned: bool = False

    model_config = ConfigDict(from_attributes=True)