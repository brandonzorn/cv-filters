import cv2
import numpy as np
from scipy import ndimage

from models import WingMask


def create_wing_mask(binary_img: np.ndarray):
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    closed = cv2.morphologyEx(binary_img, cv2.MORPH_CLOSE, kernel, iterations=2)

    filled = ndimage.binary_fill_holes(closed)
    if not isinstance(filled, np.ndarray):
        raise TypeError(f"filled is not a np.ndarray, got {type(filled)}")
    mask = (filled * 255).astype(np.uint8)

    clean = np.zeros_like(mask)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask)

    components = []
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        components.append((area, i))

    if len(components) > 0:
        components.sort(reverse=True)
        max_area = components[0][0]

        for area, i in components:
            if area > 0.3 * max_area:
                clean[labels == i] = 255

    contours, _ = cv2.findContours(clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    M = cv2.moments(clean)
    if M["m00"] != 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
    else:
        h, w = clean.shape
        cx, cy = w // 2, h // 2

    center = (cx, cy)

    return WingMask(
        original=binary_img,
        clean=clean,
        contours=contours,
        center=center,
    )
