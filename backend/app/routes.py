import os
import shutil
from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from uuid import uuid4

from database import get_db
from models import Image
from schemas import ImageResponse
from handlers import apply_filter
from settings import UPLOAD_DIR, PROCESSED_DIR

router = APIRouter(prefix="/images", tags=["images"])

@router.post("/upload", response_model=ImageResponse)
def upload_image(
    file: UploadFile = File(...),
    filter_type: str = Form(...),
    db: Session = Depends(get_db)
):

    file_id = str(uuid4())
    original_path = f"{UPLOAD_DIR}/{file_id}_{file.filename}"
    processed_path = f"{PROCESSED_DIR}/{file_id}_{file.filename}"

    with open(original_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    apply_filter(original_path, processed_path, filter_type)

    image = Image(
        original_path=original_path,
        processed_path=processed_path,
        filter_type=filter_type
    )
    db.add(image)
    db.commit()
    db.refresh(image)

    return {
        "id": image.id,
        "original_url": f"/{original_path}",
        "processed_url": f"/{processed_path}",
        "filter_type": image.filter_type,
        "created_at": image.created_at
    }


@router.get("/", response_model=list[ImageResponse])
def get_images(db: Session = Depends(get_db)):
    images = db.query(Image).order_by(Image.created_at.desc()).all()

    return [
        {
            "id": img.id,
            "original_url": f"/{img.original_path}",
            "processed_url": f"/{img.processed_path}",
            "filter_type": img.filter_type,
            "created_at": img.created_at
        }
        for img in images
    ]