from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base
from enum import StrEnum, unique

@unique
class FilterType(StrEnum):
    BLUR = "blur"
    GRAYSCALE = "grayscale"
    SOBEL = "sobel"
    THRESHOLD = "threshold"
    LAPLACIAN = "laplacian"


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String, nullable=False)
    processed_url = Column(String, nullable=False)
    filter_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)