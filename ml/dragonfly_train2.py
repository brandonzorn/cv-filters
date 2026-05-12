from collections import defaultdict
from pathlib import Path
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
    transforms.RandomRotation(10),
    # transforms.RandomRotation(180),
    # transforms.RandomHorizontalFlip(),
    # transforms.RandomVerticalFlip(),
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
    


def train_model(root_data_dir, epochs=15, batch_size=32, lr=1e-4):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Используем устройство: {device}")

    base_dataset = DragonflyDataset(root_dir=root_data_dir)
    num_species = len(base_dataset.species_to_idx)
    num_genders = len(base_dataset.gender_to_idx)
    print(f"Найдено видов: {num_species}, Полов: {num_genders}")

    specimen_to_species = {}

    for sample in base_dataset.samples:
        specimen_to_species[sample["specimen_id"]] = sample["species"]

    all_specimens = list(specimen_to_species.keys())

    all_species = [
        specimen_to_species[s]
        for s in all_specimens
    ]

    train_specimens, val_specimens = train_test_split(
        all_specimens,
        test_size=0.25,
        random_state=44,
        stratify=all_species
    )

    train_specimens = set(train_specimens)
    val_specimens = set(val_specimens)

    train_idx = [
        i for i, sample in enumerate(base_dataset.samples)
        if sample["specimen_id"] in train_specimens
    ]

    val_idx = [
        i for i, sample in enumerate(base_dataset.samples)
        if sample["specimen_id"] in val_specimens
    ]

    train_dataset = Subset(
        DragonflyDataset(
            root_dir=root_data_dir,
            transform=train_transforms
        ),
        train_idx
    )

    val_dataset = Subset(
        DragonflyDataset(
            root_dir=root_data_dir,
            transform=val_transforms
        ),
        val_idx
    )

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=2)

    model = MultiTaskDragonflyNet(num_species=num_species, num_genders=num_genders).to(device)
    
    criterion_species = nn.CrossEntropyLoss()
    criterion_gender = nn.CrossEntropyLoss()
    
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="max",
        factor=0.5,
        patience=2
    )
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        for images, species_targets, gender_targets in train_loader:
            images = images.to(device)
            species_targets = species_targets.to(device)
            gender_targets = gender_targets.to(device)

            optimizer.zero_grad()

            species_preds, gender_preds = model(images)

            loss_species = criterion_species(species_preds, species_targets)
            loss_gender = criterion_gender(gender_preds, gender_targets)
            
            total_loss = loss_species + 2.0 * loss_gender
            
            total_loss.backward()
            optimizer.step()

            running_loss += total_loss.item() * images.size(0)

        epoch_loss = running_loss / len(train_loader.dataset)
        
        model.eval()
        correct_species = 0
        correct_gender = 0
        
        with torch.no_grad():
            for images, species_targets, gender_targets in val_loader:
                images = images.to(device)
                species_targets = species_targets.to(device)
                gender_targets = gender_targets.to(device)

                species_preds, gender_preds = model(images)

                _, sp_predicted = torch.max(species_preds, 1)
                _, gen_predicted = torch.max(gender_preds, 1)
                
                correct_species += (sp_predicted == species_targets).sum().item()
                correct_gender += (gen_predicted == gender_targets).sum().item()

        val_acc_species = correct_species / len(val_loader.dataset) * 100
        val_acc_gender = correct_gender / len(val_loader.dataset) * 100

        print(f"Эпоха [{epoch+1}/{epochs}] -> Loss: {epoch_loss:.4f} | Val Acc Вид: {val_acc_species:.2f}% | Val Acc Пол: {val_acc_gender:.2f}%")
        scheduler.step(val_acc_gender)

    torch.save(model.state_dict(), "dragonfly_multitask_model.pth")
    print("Модель успешно сохранена!")


if __name__ == "__main__":
    train_model(root_data_dir=Path('photo_binary_split'), epochs=15, batch_size=32, lr=3e-4)