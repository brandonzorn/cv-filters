from pathlib import Path
from PIL import Image

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

import torchvision.transforms as T

import timm

from sklearn.model_selection import train_test_split
from tqdm import tqdm


ROOT = Path("photo_binary_split")

IMG_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 15
LR = 1e-4
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# =========================
# DATASET
# =========================

samples = []

species_names = sorted([
    p.name for p in ROOT.iterdir()
    if p.is_dir()
])

species_to_idx = {
    name: i
    for i, name in enumerate(species_names)
}

for species_dir in ROOT.iterdir():
    if not species_dir.is_dir():
        continue

    species = species_dir.name

    for gender_dir in species_dir.iterdir():
        if not gender_dir.is_dir():
            continue

        for img_path in gender_dir.glob("*.png"):
            samples.append((
                str(img_path),
                species_to_idx[species]
            ))


train_samples, val_samples = train_test_split(
    samples,
    test_size=0.2,
    stratify=[x[1] for x in samples],
    random_state=42
)


# =========================
# TRANSFORMS
# =========================

train_transform = T.Compose([
    T.Resize((IMG_SIZE, IMG_SIZE)),
    T.RandomHorizontalFlip(),
    T.RandomRotation(15),
    T.ColorJitter(
        brightness=0.1,
        contrast=0.1
    ),
    T.ToTensor(),
])

val_transform = T.Compose([
    T.Resize((IMG_SIZE, IMG_SIZE)),
    T.ToTensor(),
])


# =========================
# DATASET CLASS
# =========================

class DragonflyDataset(Dataset):
    def __init__(self, samples, transform):
        self.samples = samples
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]

        image = Image.open(path).convert("RGB")

        image = self.transform(image)

        return image, label


train_dataset = DragonflyDataset(
    train_samples,
    train_transform
)

val_dataset = DragonflyDataset(
    val_samples,
    val_transform
)


def main():
    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=4
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=4
    )


    # =========================
    # MODEL
    # =========================

    model = timm.create_model(
        "efficientnet_b0",
        pretrained=True,
        num_classes=len(species_names)
    )

    model = model.to(DEVICE)


    criterion = nn.CrossEntropyLoss()

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LR
    )


    # =========================
    # TRAIN LOOP
    # =========================

    best_acc = 0.0

    for epoch in range(EPOCHS):

        # TRAIN
        model.train()

        train_loss = 0.0

        for images, labels in tqdm(train_loader):

            images = images.to(DEVICE)
            labels = labels.to(DEVICE)

            optimizer.zero_grad()

            outputs = model(images)

            loss = criterion(outputs, labels)

            loss.backward()

            optimizer.step()

            train_loss += loss.item()

        # VALIDATION
        model.eval()

        correct = 0
        total = 0

        with torch.no_grad():

            for images, labels in val_loader:

                images = images.to(DEVICE)
                labels = labels.to(DEVICE)

                outputs = model(images)

                preds = outputs.argmax(dim=1)

                correct += (preds == labels).sum().item()
                total += labels.size(0)

        acc = correct / total

        print(
            f"Epoch {epoch+1} | "
            f"loss={train_loss:.4f} | "
            f"val_acc={acc:.4f}"
        )

        if acc > best_acc:
            best_acc = acc

            torch.save({
                "model_state": model.state_dict(),
                "species_to_idx": species_to_idx,
            }, "best_model.pt")

            print("Model saved!")


if __name__ == "__main__":
    main()
