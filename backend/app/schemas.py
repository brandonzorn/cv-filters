from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DragonflyResponse(BaseModel):
    id: int
    species_name: str
    gender: str
    created_at: datetime

    class Config:
        from_attributes = True


class ImageResponse(BaseModel):
    id: int
    original_url: str
    processed_url: str
    thumbnail_url: str
    filter_type: str
    created_at: datetime
    data: Optional[str] = None

    dragonfly: DragonflyResponse

    class Config:
        from_attributes = True