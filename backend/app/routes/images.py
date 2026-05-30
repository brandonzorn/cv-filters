import json
import shutil
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session
from PIL import Image as PILImage
from uuid import uuid4

from database import get_db
from models import Dragonfly, Image
from schemas import ImageResponse
from handlers import apply_filter
from settings import UPLOAD_DIR, PROCESSED_DIR

router = APIRouter(prefix="/images", tags=["images"])

def generate_thumbnail(source_path: str, dest_path: str):
    with PILImage.open(source_path) as img:
        width, height = img.size
        
        if width >= height:
            max_size = (1280, 720)
        else:
            max_size = (720, 1280)

        img.thumbnail(max_size, PILImage.Resampling.LANCZOS)
        img.save(dest_path, optimize=True, quality=85)

@router.post("/upload", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
def upload_image(
    file: UploadFile = File(...),
    filter_type: str = Form(...),
    extra_params: str = Form(...),
    db: Session = Depends(get_db)
):
    additional_args = {}
    if extra_params:
        try:
            additional_args = json.loads(extra_params)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="extra_params must be a valid JSON string")

    if not file.filename:
        raise ValueError("can't find file")
    
    file_ext = file.filename.rsplit(".")[-1]

    file_id = str(uuid4())
    original_url = f"{UPLOAD_DIR}/{file_id}.{file_ext}"
    processed_url = f"{PROCESSED_DIR}/{file_id}.jpg"
    thumbnail_url = f"{PROCESSED_DIR}/{file_id}_thumb.jpg"

    with open(original_url, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    predicted_species, predicted_gender = apply_filter(original_url, filter_type, **additional_args)
    generate_thumbnail(original_url, thumbnail_url)
    
    dragonfly = Dragonfly(
        species_name=predicted_species,
        gender=predicted_gender,
    )
    db.add(dragonfly)
    db.flush()

    image = Image(
        original_url=original_url,
        processed_url=processed_url,
        thumbnail_url=thumbnail_url,
        filter_type=filter_type,
        dragonfly_id=dragonfly.id,
    )
    db.add(image)
    db.commit()
    db.refresh(image)

    return image


@router.get("/", response_model=list[ImageResponse])
def get_images(db: Session = Depends(get_db)):
    images = db.query(Image).order_by(Image.created_at.desc()).all()

    return images
