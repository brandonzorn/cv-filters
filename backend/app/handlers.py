import cv2

from filters import dragonfly_torch1
from filters import dragonfly
from models import FilterType



def apply_filter(input_path: str, filter_type: str, **params):
    img = cv2.imread(input_path)
    if img is None:
        raise RuntimeError("Can't load image")

    f_type = FilterType(filter_type)

    match f_type:
        case FilterType.DRAGONFLY:
            splitted = dragonfly.process_dragonfly_image(img)
            return dragonfly_torch1.predict_image_cv2(splitted[0])
        case _:
            raise ValueError("Unknown filter")
