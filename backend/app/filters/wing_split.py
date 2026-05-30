import cv2
import numpy as np
from skimage.graph import route_through_array

from models import WingMask


def _farthest_point(group: np.ndarray, center: tuple[int, int]):
    if len(group) == 0:
        return None
    distances = np.linalg.norm(group - center, axis=1)
    idx = np.argmax(distances)
    return tuple(group[idx])


def splitting(wing_mask: WingMask):
    original = wing_mask.original
    mask = wing_mask.clean
    contours = wing_mask.contours

    all_points = np.vstack(contours)
    points = all_points.squeeze()

    center = wing_mask.center
    cx, cy = center

    x_min, y_min = points.min(axis=0)
    x_max, y_max = points.max(axis=0)

    y_split = (y_min + y_max) // 2

    left_points = points[points[:, 0] < cx]
    right_points = points[points[:, 0] >= cx]

    left_top_points = left_points[left_points[:, 1] < y_split]
    left_bottom_points = left_points[left_points[:, 1] >= y_split]

    right_top_points = right_points[right_points[:, 1] < y_split]
    right_bottom_points = right_points[right_points[:, 1] >= y_split]

    lt = _farthest_point(left_top_points, center)
    lb = _farthest_point(left_bottom_points, center)
    rt = _farthest_point(right_top_points, center)
    rb = _farthest_point(right_bottom_points, center)

    if any(p is None for p in [lt, lb, rt, rb]):
        raise ValueError(
            f"Could not detect all wing tips: lt={lt}, lb={lb}, rt={rt}, rb={rb}"
        )

    left_mid = ((lt[0] + lb[0]) // 2, (lt[1] + lb[1]) // 2)
    right_mid = ((rt[0] + rb[0]) // 2, (rt[1] + rb[1]) // 2)

    left_width = int(np.linalg.norm(np.array(lt) - np.array(lb)))
    right_width = int(np.linalg.norm(np.array(rt) - np.array(rb)))
    left_corridor_width = max(20, int(left_width * 0.35))
    right_corridor_width = max(20, int(right_width * 0.35))

    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    cost = dist.astype(np.float64) * 30
    cost[mask == 0] = 1

    start = (cy, cx)
    left_end = (left_mid[1], left_mid[0])
    right_end = (right_mid[1], right_mid[0])

    left_corridor = np.zeros_like(mask)
    cv2.line(left_corridor, (cx, cy), left_mid, 255, left_corridor_width)
    left_cost = cost.copy()
    left_cost[left_corridor == 0] = 1e6

    right_corridor = np.zeros_like(mask)
    cv2.line(right_corridor, (cx, cy), right_mid, 255, right_corridor_width)
    right_cost = cost.copy()
    right_cost[right_corridor == 0] = 1e6

    left_path, _ = route_through_array(left_cost, start, left_end, fully_connected=True)
    right_path, _ = route_through_array(
        right_cost, start, right_end, fully_connected=True
    )

    path_mask = np.zeros_like(mask)
    combined_path = []
    for y, x in reversed(left_path):
        combined_path.append((x, y))
    for y, x in right_path:
        combined_path.append((x, y))

    pts = np.array(combined_path, dtype=np.int32)

    h, w = mask.shape
    polygon = np.vstack([pts, [[w - 1, h - 1], [0, h - 1]]])
    cv2.fillPoly(path_mask, [polygon], 255)

    left_side = np.zeros_like(mask)
    left_side[:, :cx] = 255
    right_side = np.zeros_like(mask)
    right_side[:, cx:] = 255

    left_top_mask = cv2.bitwise_and(cv2.bitwise_not(path_mask), left_side, mask=mask)
    left_bottom_mask = cv2.bitwise_and(path_mask, left_side, mask=mask)
    right_top_mask = cv2.bitwise_and(cv2.bitwise_not(path_mask), right_side, mask=mask)
    right_bottom_mask = cv2.bitwise_and(path_mask, right_side, mask=mask)

    wing_masks = [left_top_mask, left_bottom_mask, right_top_mask, right_bottom_mask]

    cropped_wings = []

    for m in wing_masks:
        ys, xs = np.where(m > 0)
        if len(xs) == 0 or len(ys) == 0:
            cropped_wings.append(None)
            continue

        x_min_m, x_max_m = xs.min(), xs.max()
        y_min_m, y_max_m = ys.min(), ys.max()

        wing = cv2.bitwise_and(original, original, mask=m)
        cropped = wing[y_min_m : y_max_m + 1, x_min_m : x_max_m + 1]
        cropped_wings.append(cropped)

    return cropped_wings
