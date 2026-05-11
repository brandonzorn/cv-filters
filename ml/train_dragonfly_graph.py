from pathlib import Path

import cv2
import joblib
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder


DATASET_DIR = Path("Photo")
MODEL_PATH = "dragonfly_graph_model.pkl"
LABEL_ENCODER_PATH = "label_encoder.pkl"


# ============================================================
# IMAGE PROCESSING
# ============================================================


def load_image(path: str | Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError(f"Cannot load image: {path}")

    return image



def remove_background(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    _, mask = cv2.threshold(
        gray,
        240,
        255,
        cv2.THRESH_BINARY_INV,
    )

    kernel = np.ones((3, 3), np.uint8)

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel,
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel,
    )

    return mask



def enhance_veins(mask: np.ndarray) -> np.ndarray:
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    enhanced = clahe.apply(mask)

    enhanced = cv2.GaussianBlur(
        enhanced,
        (3, 3),
        0,
    )

    veins = cv2.adaptiveThreshold(
        enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        5,
    )

    kernel = np.ones((2, 2), np.uint8)

    veins = cv2.morphologyEx(
        veins,
        cv2.MORPH_OPEN,
        kernel,
    )

    return veins



def create_skeleton(binary: np.ndarray) -> np.ndarray:
    skeleton = cv2.ximgproc.thinning(binary)
    return skeleton.astype(np.uint8)


# ============================================================
# GRAPH CREATION
# ============================================================


def neighbors(y: int, x: int, image: np.ndarray):
    h, w = image.shape

    result = []

    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue

            ny = y + dy
            nx_ = x + dx

            if 0 <= ny < h and 0 <= nx_ < w:
                if image[ny, nx_] > 0:
                    result.append((ny, nx_))

    return result



def compute_node_maps(skeleton: np.ndarray):
    s = skeleton.astype(np.uint8)
    kernel = np.array([
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1]
    ], dtype=np.uint8)

    degree = cv2.filter2D(s, -1, kernel)

    junctions = (s == 1) & (degree > 2)
    endpoints = (s == 1) & (degree == 1)

    return degree, junctions, endpoints



# ============================================================
# FEATURE EXTRACTION
# ============================================================


def extract_features(image: np.ndarray) -> np.ndarray:
    mask = remove_background(image)

    veins = enhance_veins(mask)

    skeleton = create_skeleton(veins)

    degree, junctions, endpoints = compute_node_maps(skeleton)

    features: list[float] = []

    skeleton_pixels = np.count_nonzero(skeleton)

    junction_count = np.count_nonzero(junctions)

    endpoint_count = np.count_nonzero(endpoints)

    mask_area = np.count_nonzero(mask)

    features.extend([skeleton_pixels, junction_count, endpoint_count, mask_area])


    valid_degrees = degree[skeleton > 0]

    degree_hist = np.bincount(
        np.clip(valid_degrees, 0, 8),
        minlength=9,
    )

    degree_hist = degree_hist.astype(np.float32)

    degree_hist /= max(degree_hist.sum(), 1)

    features.extend(degree_hist.tolist())


    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        skeleton,
        connectivity=8,
    )

    component_sizes = stats[:, cv2.CC_STAT_AREA]

    features.extend([
        num_labels,
        component_sizes.mean(),
        component_sizes.std(),
        component_sizes.max(),
    ])


    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    if contours:
        largest = max(contours, key=cv2.contourArea)

        area = cv2.contourArea(largest)

        perimeter = cv2.arcLength(largest, True)

        x, y, w, h = cv2.boundingRect(largest)

        aspect_ratio = w / max(h, 1)

        hull = cv2.convexHull(largest)

        hull_area = cv2.contourArea(hull)

        solidity = area / max(hull_area, 1)

        features.extend([
            area,
            perimeter,
            aspect_ratio,
            solidity,
        ])
    else:
        features.extend([0, 0, 0, 0])


    gx = cv2.Sobel(
        skeleton,
        cv2.CV_32F,
        1,
        0,
        ksize=3,
    )

    gy = cv2.Sobel(
        skeleton,
        cv2.CV_32F,
        0,
        1,
        ksize=3,
    )

    angles = np.arctan2(gy, gx)

    angles = angles[skeleton > 0]

    if len(angles) > 0:
        hist, _ = np.histogram(
            angles,
            bins=16,
            range=(-np.pi, np.pi),
        )

        hist = hist.astype(np.float32)

        hist /= max(hist.sum(), 1)

        features.extend(hist.tolist())
    else:
        features.extend([0] * 16)

    features = np.array(features, dtype=np.float32)

    return features


# ============================================================
# DATASET
# ============================================================


def process_image(path: str | Path) -> np.ndarray:
    image = load_image(path)

    return extract_features(image)



def load_dataset(dataset_dir: Path):
    X = []
    y = []

    for species_dir in dataset_dir.iterdir():
        if not species_dir.is_dir():
            continue

        species_name = species_dir.name

        print(f"Processing species: {species_name}")

        for image_path in species_dir.glob("*"):
            try:
                features = process_image(image_path)

                X.append(features)
                y.append(species_name)

                print(f"  OK: {image_path.name}")

            except Exception as error:
                print(f"  ERROR: {image_path.name}: {error}")

    return np.array(X), np.array(y)


# ============================================================
# TRAINING
# ============================================================


def train_model():
    X, y = load_dataset(DATASET_DIR)

    print()
    print(f"Samples: {len(X)}")
    print(f"Classes: {len(set(y))}")
    print()

    label_encoder = LabelEncoder()

    y_encoded = label_encoder.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y_encoded,
        test_size=0.2,
        random_state=42,
        stratify=y_encoded,
    )

    model = RandomForestClassifier(
        n_estimators=500,
        max_depth=None,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    print(classification_report(
        y_test,
        predictions,
        target_names=label_encoder.classes_,
    ))

    joblib.dump(model, MODEL_PATH)
    joblib.dump(label_encoder, LABEL_ENCODER_PATH)

    print()
    print("Model saved")


# ============================================================
# PREDICTION
# ============================================================


def predict_image(image_path: str | Path):
    model = joblib.load(MODEL_PATH)
    label_encoder = joblib.load(LABEL_ENCODER_PATH)

    features = process_image(image_path)

    prediction = model.predict([features])[0]

    species = label_encoder.inverse_transform([prediction])[0]

    probabilities = model.predict_proba([features])[0]

    confidence = np.max(probabilities)

    print()
    print(f"Predicted species: {species}")
    print(f"Confidence: {confidence:.4f}")


# ============================================================
# VISUALIZATION
# ============================================================


def visualize_pipeline(image_path: str | Path):
    image = load_image(image_path)

    mask = remove_background(image)

    veins = enhance_veins(mask)

    skeleton = create_skeleton(veins)

    _, junctions, endpoints = compute_node_maps(skeleton)

    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 3, figsize=(16, 10))

    axes[0, 0].imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    axes[0, 0].set_title("Original")

    axes[0, 1].imshow(mask, cmap="gray")
    axes[0, 1].set_title("Mask")

    axes[0, 2].imshow(veins, cmap="gray")
    axes[0, 2].set_title("Veins")

    axes[1, 0].imshow(skeleton, cmap="gray")
    axes[1, 0].set_title("Skeleton")

    axes[1, 1].imshow(junctions, cmap="hot")
    axes[1, 1].set_title("Junctions")

    axes[1, 2].imshow(endpoints, cmap="hot")
    axes[1, 2].set_title("Endpoints")

    for ax in axes.ravel():
        ax.axis("off")

    plt.tight_layout()
    plt.show()


# ============================================================
# MAIN
# ============================================================


if __name__ == "__main__":
    train_model()

    # Example:
    # predict_image("test.jpg")

    # visualize_pipeline("test.jpg")
