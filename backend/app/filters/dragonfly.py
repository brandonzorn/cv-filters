import cv2
import numpy as np


def remove_background(gray: np.ndarray) -> np.ndarray:
    mask = cv2.threshold(
        gray,
        250,
        255,
        cv2.THRESH_BINARY_INV,
    )[1]

    kernel = np.ones((3, 3), np.uint8)

    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return mask


def enhance_contrast(gray: np.ndarray) -> np.ndarray:
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )
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


def extract_veins_for_wing(enhanced_gray: np.ndarray, wing_mask: np.ndarray) -> np.ndarray:
    """
    Извлекает жилки внутри конкретного крыла.
    Порог адаптируется локально — только по пикселям крыла.
    """
    blurred = cv2.GaussianBlur(enhanced_gray, (3, 3), 0)
    veins = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 31, 10,
    )
    veins_masked = cv2.bitwise_and(veins, veins, mask=wing_mask)
    kernel = np.ones((2, 2), np.uint8)
    return cv2.morphologyEx(veins_masked, cv2.MORPH_OPEN, kernel)


def get_wing_masks(mask: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Возвращает 4 бинарные маски силуэтов крыльев по квадрантам.
    """
    h, w = mask.shape

    m = cv2.moments(mask)
    if m["m00"] == 0:
        empty = np.zeros((h, w), dtype=np.uint8)
        return empty, empty, empty, empty

    cx = int(m["m10"] / m["m00"])
    cy = int(m["m01"] / m["m00"])

    quadrants = [
        (slice(0, cy), slice(0, cx)),
        (slice(0, cy), slice(cx, w)),
        (slice(cy, h), slice(0, cx)),
        (slice(cy, h), slice(cx, w)),
    ]

    result = []
    for row_sl, col_sl in quadrants:
        region = mask[row_sl, col_sl]
        n, labels, stats, _ = cv2.connectedComponentsWithStats(region, connectivity=8)

        wing_mask = np.zeros((h, w), dtype=np.uint8)
        if n > 1:
            best = int(np.argmax(stats[1:, cv2.CC_STAT_AREA])) + 1
            component = np.zeros_like(region)
            component[labels == best] = 255
            wing_mask[row_sl, col_sl] = component

        result.append(wing_mask)

    return tuple(result)


def process_dragonfly_image(image: np.ndarray):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mask = remove_background(gray)
    enhanced = enhance_contrast(gray)
    veins = extract_veins(enhanced, mask)
    wings = get_wing_masks(mask)
    for i, w in enumerate(wings):
        cv2.imwrite(f"{i}.png", w)
    return veins


__all__ = ["process_dragonfly_image"]
