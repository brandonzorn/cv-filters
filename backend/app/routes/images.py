import shutil
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import uuid4

from database import get_db
from models import Image
from schemas import ImageResponse
from handlers import apply_filter
from settings import UPLOAD_DIR, PROCESSED_DIR

router = APIRouter(prefix="/images", tags=["images"])

@router.post("/upload", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
def upload_image(
    file: UploadFile = File(...),
    filter_type: str = Form(...),
    db: Session = Depends(get_db)
):

    file_id = str(uuid4())
    original_url = f"{UPLOAD_DIR}/{file_id}_{file.filename}"
    processed_url = f"{PROCESSED_DIR}/{file_id}_{file.filename}"

    with open(original_url, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        apply_filter(original_url, processed_url, filter_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filter type")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error processing image")

    image = Image(
        original_url=original_url,
        processed_url=processed_url,
        filter_type=filter_type
    )
    db.add(image)
    db.commit()
    db.refresh(image)

    return image


@router.get("/", response_model=list[ImageResponse])
def get_images(db: Session = Depends(get_db)):
    images = db.query(Image).order_by(Image.created_at.desc()).all()

    return images
