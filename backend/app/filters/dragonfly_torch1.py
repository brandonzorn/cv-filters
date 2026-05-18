from collections import defaultdict
from pathlib import Path
import cv2
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, Subset
from torchvision import transforms, models
from PIL import Image
from sklearn.model_selection import train_test_split

train_transforms = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((224, 224)),
    # transforms.RandomRotation(10),
    transforms.RandomRotation(180),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5], std=[0.5])
])

val_transforms = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5], std=[0.5])
])


class DragonflyDataset(Dataset):
    def __init__(self, root_dir: Path, transform=None):
        self.transform = transform
        self.samples = []

        self.species_to_idx = {}
        self.gender_to_idx = {}

        species_dirs = sorted([
            p for p in root_dir.iterdir()
            if p.is_dir()
        ])

        for species_idx, species_path in enumerate(species_dirs):

            self.species_to_idx[species_path.name] = species_idx

            gender_dirs = sorted([
                p for p in species_path.iterdir()
                if p.is_dir()
            ])

            for gender_path in gender_dirs:

                gender_name = gender_path.name

                if gender_name not in self.gender_to_idx:
                    self.gender_to_idx[gender_name] = len(self.gender_to_idx)

                image_files = sorted([
                    p for p in gender_path.iterdir()
                    if p.suffix.lower() in [".png", ".jpg", ".jpeg"]
                ])

                for img_path in image_files:

                    stem = img_path.stem

                    parts = stem.rsplit("_", 1)
                    if len(parts) != 2:
                        continue
                    specimen_id = parts[0]
                    self.samples.append({
                        "image": img_path,
                        "species": species_idx,
                        "gender": self.gender_to_idx[gender_name],
                        "specimen_id": specimen_id
                    })

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):

        sample = self.samples[idx]

        image = Image.open(sample["image"]).convert("L")

        if self.transform:
            image = self.transform(image)

        return (
            image,
            torch.tensor(sample["species"], dtype=torch.long),
            torch.tensor(sample["gender"], dtype=torch.long)
        )
    


class MultiTaskDragonflyNet(nn.Module):
    def __init__(self, num_species, num_genders=2):
        super().__init__()

        backbone = models.efficientnet_b0(
            weights=models.EfficientNet_B0_Weights.DEFAULT
        )

        backbone.features[0][0] = nn.Conv2d(
            1,
            32,
            kernel_size=3,
            stride=2,
            padding=1,
            bias=False
        )

        in_features = backbone.classifier[1].in_features
        backbone.classifier = nn.Identity()

        self.backbone = backbone

        self.species_head = nn.Sequential(
            nn.Linear(in_features, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_species)
        )

        self.gender_head = nn.Sequential(
            nn.Linear(in_features, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, num_genders)
        )

    def forward(self, x):

        features = self.backbone(x)

        species = self.species_head(features)
        gender = self.gender_head(features)

        return species, gender


def predict_image_cv2(
    cv2_image,
    model_path="dragonfly_multitask_model.pth"
):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    checkpoint = torch.load(model_path, map_location=device)

    species_to_idx = checkpoint["species_to_idx"]
    gender_to_idx = checkpoint["gender_to_idx"]

    idx_to_species = {
        v: k for k, v in species_to_idx.items()
    }

    idx_to_gender = {
        v: k for k, v in gender_to_idx.items()
    }

    num_species = len(species_to_idx)
    num_genders = len(gender_to_idx)

    model = MultiTaskDragonflyNet(
        num_species=num_species,
        num_genders=num_genders
    ).to(device)

    model.load_state_dict(checkpoint["model_state_dict"])

    model.eval()

    if len(cv2_image.shape) == 3:
        cv2_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)

    pil_image = Image.fromarray(cv2_image)

    image = val_transforms(pil_image)

    image = image.unsqueeze(0).to(device)

    with torch.no_grad():
        species_logits, gender_logits = model(image)

        species_pred = torch.argmax(species_logits, dim=1).item()
        gender_pred = torch.argmax(gender_logits, dim=1).item()

    predicted_species = idx_to_species[species_pred]
    predicted_gender = idx_to_gender[gender_pred]

    return predicted_species, predicted_gender

if __name__ == "__main__":
    print(predict_image("./ASU_ZCIN_OD0357_4.png", "dragonfly_multitask_model.pth"))