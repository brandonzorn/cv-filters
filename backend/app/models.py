from dataclasses import dataclass

import cv2
import numpy as np
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from enum import StrEnum, unique


@dataclass
class WingMask:
    original: np.ndarray
    clean: np.ndarray
    contours: tuple[cv2.typing.MatLike]
    center: tuple[int, int]


@unique
class FilterType(StrEnum):
    DRAGONFLY = "dragonfly"


class Dragonfly(Base):
    __tablename__ = "dragonflies"

    id = Column(Integer, primary_key=True, index=True)
    species_name = Column(String, nullable=False)
    gender = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    images = relationship(
        "Image", back_populates="dragonfly", cascade="all, delete-orphan"
    )


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    dragonfly_id = Column(Integer, ForeignKey("dragonflies.id"), nullable=False)

    original_url = Column(String, nullable=False)
    processed_url = Column(String, nullable=False)
    thumbnail_url = Column(String, nullable=False)
    filter_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    dragonfly = relationship("Dragonfly", back_populates="images")
