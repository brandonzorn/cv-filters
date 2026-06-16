from fastapi import APIRouter
from models import FilterType

router = APIRouter(prefix="/constants", tags=["constants"])

@router.get("/filters", response_model=list[str])
def get_available_filters():
    return [f.value for f in FilterType]