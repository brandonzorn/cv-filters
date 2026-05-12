from pathlib import Path

import cv2
import numpy as np


def convert_to_binary(gray: np.ndarray) -> np.ndarray:
    _, binary = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY_INV)
    return binary


def remove_background(binary: np.ndarray) -> np.ndarray:
    kernel_body = np.ones((16, 16), np.uint8)
    body_mask = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_body)
    body_mask = cv2.dilate(body_mask, np.ones((5, 5), np.uint8), iterations=1)
    wings_grid = cv2.subtract(binary, body_mask)
    return wings_grid


def enhance_contrast(gray: np.ndarray) -> np.ndarray:
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
    return clahe.apply(gray)


def extract_veins(enhanced_gray: np.ndarray, mask: np.ndarray) -> np.ndarray:
    blurred = cv2.GaussianBlur(enhanced_gray, (3, 3), 0)

    veins = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 
        31,
        10,
    )
    veins_masked = cv2.bitwise_and(veins, veins, mask=mask)

    kernel = np.ones((2, 2), np.uint8)
    veins_cleaned = cv2.morphologyEx(veins_masked, cv2.MORPH_OPEN, kernel)
    return veins_cleaned


def process_dragonfly_image(image: np.ndarray):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    binary = convert_to_binary(gray)
    mask = remove_background(binary)
    enhanced = enhance_contrast(gray)
    veins = extract_veins(enhanced, mask)

    return veins

def process_directory(source_path, output_path):
    source = Path(source_path)
    output = Path(output_path)

    for file in source.rglob('*'):
        if file.is_file():
            relative_path = file.relative_to(source)
            target_file_path = output / relative_path
            target_file_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                print(file.absolute())
                print(target_file_path.absolute())
                img = cv2.imread(file.absolute())
                if img is None:
                    raise RuntimeError
                result = process_dragonfly_image(img)
                
                cv2.imwrite(target_file_path.absolute(), result)
                    
                print(f"Обработан: {relative_path}")
            except Exception as e:
                print(f"Ошибка при обработке {relative_path}: {e}")


process_directory('./ml/Photo', './ml/photo_binary')