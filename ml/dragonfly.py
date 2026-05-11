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

    # mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    # mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
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


def split_wings(mask: np.ndarray):

    kernel = np.ones((3, 3), np.uint8)
    dist = cv2.distanceTransform(
        mask,
        cv2.DIST_L2,
        5,
    )

    dist_norm = np.zeros_like(dist)

    cv2.normalize(
        dist,
        dist_norm,
        0,
        1.0,
        cv2.NORM_MINMAX,
    )

    _, sure_fg = cv2.threshold(
        dist_norm,
        0.25,
        1.0,
        cv2.THRESH_BINARY,
    )

    sure_fg = (sure_fg * 255).astype(np.uint8)
    sure_bg = cv2.dilate(mask, kernel, iterations=3)

    unknown = cv2.subtract(sure_bg, sure_fg)
    num_markers, markers = cv2.connectedComponents(sure_fg)

    markers = markers + 1
    markers[unknown == 255] = 0
    markers = cv2.watershed(mask, markers)

    wings = []

    for label in np.unique(markers):

        if label <= 1:
            continue

        wing_mask = np.zeros_like(mask)

        wing_mask[markers == label] = 255

        area = cv2.countNonZero(wing_mask)
        if area < 3000:
            continue

        x, y, w, h = cv2.boundingRect(wing_mask)

        cropped_mask = wing_mask[y:y+h, x:x+w]

        wings.append(cropped_mask)

    return wings


def process_dragonfly_image(image: np.ndarray):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mask = remove_background(gray)
    enhanced = enhance_contrast(gray)
    veins = extract_veins(enhanced, mask)
    
    return gray, mask, enhanced, veins



img = cv2.imread(r"Photo\Orthetrum albistylum\ASU_ZCIN_OD2815.jpg")
if img is None:
    raise RuntimeError
gray, mask, enhanced, veins = process_dragonfly_image(img)
cv2.imwrite("g.png", veins)
cv2.imshow('0', cv2.resize(gray, (1366, 768), interpolation=cv2.INTER_AREA))
cv2.imshow('1', cv2.resize(mask, (1366, 768), interpolation=cv2.INTER_AREA))
cv2.imshow('2', cv2.resize(enhanced, (1366, 768), interpolation=cv2.INTER_AREA))
cv2.imshow('3', cv2.resize(veins, (1366, 768), interpolation=cv2.INTER_AREA))
cv2.waitKey()
