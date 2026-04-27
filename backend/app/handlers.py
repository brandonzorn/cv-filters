import cv2

from models import FilterType


def apply_filter(input_path: str, output_path: str, filter_type: str, **params):
    img = cv2.imread(input_path)

    f_type = FilterType(filter_type)

    match f_type:
        case FilterType.BLUR:
            k_size: int = int(params.get("kernel_size", 15))
            if k_size % 2 != 0:
                raise ValueError("kernel_size must be an odd integer")
            result = cv2.GaussianBlur(img, (k_size, k_size), 0)
        case FilterType.GRAYSCALE:
            threshold1: float = float(params.get("threshold1", 100))
            threshold2: float = float(params.get("threshold2", 200))
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            result = cv2.Canny(gray, threshold1, threshold2)
        case FilterType.SOBEL:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            result = cv2.Sobel(gray, cv2.CV_64F, 1, 1, ksize=5)
        case FilterType.THRESHOLD:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, result = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        case FilterType.LAPLACIAN:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            result = cv2.Laplacian(gray, cv2.CV_64F)
        case _:
            raise ValueError("Unknown filter")

    cv2.imwrite(output_path, result)
