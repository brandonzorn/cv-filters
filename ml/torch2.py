import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, Subset
from torchvision import transforms, models
from PIL import Image
from sklearn.model_selection import train_test_split

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


def predict_image(
    image_path,
    model_path,
    root_data_dir
):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Загружаем dataset только чтобы восстановить mapping
    dataset = DragonflyDataset(root_dir=root_data_dir)

    idx_to_species = {
        v: k for k, v in dataset.species_to_idx.items()
    }

    idx_to_gender = {
        v: k for k, v in dataset.gender_to_idx.items()
    }

    num_species = len(dataset.species_to_idx)
    num_genders = len(dataset.gender_to_idx)

    # Создаем модель
    model = MultiTaskDragonflyNet(
        num_species=num_species,
        num_genders=num_genders
    ).to(device)

    # Загружаем веса
    model.load_state_dict(
        torch.load(model_path, map_location=device)
    )

    model.eval()

    # Трансформации как на validation
    transform = val_transforms

    # Загружаем изображение
    image = Image.open(image_path).convert("L")
    image = transform(image)

    # Добавляем batch dimension
    image = image.unsqueeze(0).to(device)

    with torch.no_grad():
        species_logits, gender_logits = model(image)

        species_pred = torch.argmax(species_logits, dim=1).item()
        gender_pred = torch.argmax(gender_logits, dim=1).item()

    predicted_species = idx_to_species[species_pred]
    predicted_gender = idx_to_gender[gender_pred]

    return predicted_species, predicted_gender