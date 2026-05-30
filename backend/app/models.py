from dataclasses import dataclass

import cv2
import numpy as np
from sqlalchemy import Column, Integer, String, DateTime
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
    created_at = Column(DateTime, default=datetime.now)


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String, nullable=False)
    processed_url = Column(String, nullable=False)
    filter_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    data = Column(String)
