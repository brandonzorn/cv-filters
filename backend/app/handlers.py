import cv2

from models import FilterType

def apply_filter(input_path: str, output_path: str, filter_type: str):
    img = cv2.imread(input_path)

    filter_type = FilterType(filter_type)

    match filter_type:
        case FilterType.BLUR:
            result = cv2.GaussianBlur(img, (15, 15), 0)
        case FilterType.GRAYSCALE:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            result = cv2.Canny(gray, 100, 200)
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