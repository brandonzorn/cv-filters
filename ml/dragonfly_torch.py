import cv2
import numpy as np
import torch
from torchvision import transforms
import timm

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

checkpoint = torch.load("best_model.pt", map_location=DEVICE)

species_to_idx = checkpoint["species_to_idx"]

idx_to_species = {
    v: k
    for k, v in species_to_idx.items()
}

model = timm.create_model(
    "efficientnet_b0",
    pretrained=False,
    num_classes=len(species_to_idx)
)

model.load_state_dict(checkpoint["model_state"])

model.to(DEVICE)
model.eval()

transform = transforms.Compose(
    [
        transforms.ToPILImage(),
        transforms.Resize((224, 224)), 
        transforms.ToTensor(),
    ],
)

def get_image_class(image: np.ndarray):
    x = transform(image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        pred = model(x).argmax(dim=1).item()

    return idx_to_species[pred]


img = cv2.imread(
    r"D:\Projects\GitHub\cv-filters\ml\photo_binary_split\Orthetrum albistylum\ASU_ZCIN_OD0357_1.png", 
    cv2.IMREAD_COLOR_RGB,
)
if img is None:
    raise RuntimeError
print(get_image_class(img))