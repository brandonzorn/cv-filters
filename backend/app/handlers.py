import cv2

from filters import dragonfly
from filters import dragonfly_torch1
from models import FilterType



def apply_filter(input_path: str, output_path: str, filter_type: str, **params):
    img = cv2.imread(input_path)
    if img is None:
        raise RuntimeError("Can't load image")

    f_type = FilterType(filter_type)

    match f_type:
        case FilterType.BLUR:
            return dragonfly_torch1.predict_image_cv2(img)
        case _:
            raise ValueError("Unknown filter")
