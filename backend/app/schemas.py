from pydantic import BaseModel
from datetime import datetime

class ImageResponse(BaseModel):
    id: int
    original_url: str
    processed_url: str
    filter_type: str
    created_at: datetime

    class Config:
        from_attributes = True