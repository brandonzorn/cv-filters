import cv2

def apply_filter(input_path: str, output_path: str, filter_type: str):
    img = cv2.imread(input_path)

    if filter_type == "blur":
        result = cv2.GaussianBlur(img, (15, 15), 0)

    elif filter_type == "grayscale":
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        result = cv2.Canny(gray, 100, 200)

    elif filter_type == "sobel":
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        result = cv2.Sobel(gray, cv2.CV_64F, 1, 1, ksize=5)

    elif filter_type == "threshold":
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, result = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

    elif filter_type == "laplacian":
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        result = cv2.Laplacian(gray, cv2.CV_64F)

    else:
        raise ValueError("Unknown filter")

    cv2.imwrite(output_path, result)