import cv2
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image

val_transforms = transforms.Compose(
    [
        transforms.Grayscale(num_output_channels=1),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5], std=[0.5]),
    ]
)


class MultiTaskDragonflyNet(nn.Module):
    def __init__(self, num_species, num_genders=2):
        super().__init__()
        backbone = models.efficientnet_b0(weights=None)

        backbone.features[0][0] = nn.Conv2d(1, 32, kernel_size=3, stride=2, padding=1, bias=False)

        in_features = backbone.classifier[1].in_features
        backbone.classifier = nn.Identity()
        self.backbone = backbone

        self.species_head = nn.Sequential(
            nn.Linear(in_features, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_species),
        )
        self.gender_head = nn.Sequential(
            nn.Linear(in_features, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, num_genders),
        )

    def forward(self, x):
        features = self.backbone(x)
        return self.species_head(features), self.gender_head(features)


def predict_image_cv2(cv2_image, model_path="models/dragonfly_multitask_model.pth"):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(model_path, map_location=device)

    idx_to_species = {v: k for k, v in checkpoint["species_to_idx"].items()}
    idx_to_gender = {v: k for k, v in checkpoint["gender_to_idx"].items()}

    model = MultiTaskDragonflyNet(
        num_species=len(idx_to_species), num_genders=len(idx_to_gender)
    ).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    if len(cv2_image.shape) == 3:
        cv2_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(cv2_image)

    image = val_transforms(pil_image).unsqueeze(0).to(device)

    with torch.no_grad():
        species_logits, gender_logits = model(image)
        species_pred = torch.argmax(species_logits, dim=1).item()
        gender_pred = torch.argmax(gender_logits, dim=1).item()

    return idx_to_species[species_pred], idx_to_gender[gender_pred]
