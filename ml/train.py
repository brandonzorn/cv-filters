import torch
import torch.nn.functional as F

from torch_geometric.loader import DataLoader
from torch_geometric.nn import (
    GCNConv,
    GraphConv,
    GATConv,
    global_mean_pool,
    BatchNorm,
)
from torch_geometric.nn import knn_graph

# =========================================================
# DATA
# =========================================================

data_pack = torch.load(
    "./dragonfly_full_data.pt",
    weights_only=False,
)

dataset = data_pack["samples"]
species_map = data_pack["species_map"]

num_classes = len(species_map)

# Удаляем пустые графы
dataset = [d for d in dataset if d.x.size(0) > 0]

torch.manual_seed(42)

indices = torch.randperm(len(dataset))

split = int(len(dataset) * 0.8)

train_dataset = [dataset[i] for i in indices[:split]]
test_dataset = [dataset[i] for i in indices[split:]]

train_loader = DataLoader(
    train_dataset,
    batch_size=4,
    shuffle=True,
)

test_loader = DataLoader(
    test_dataset,
    batch_size=4,
    shuffle=False,
)

# =========================================================
# MODEL
# =========================================================

class DragonflyGNN(torch.nn.Module):

    def __init__(self, in_channels, hidden_channels, num_classes):
        super().__init__()

        self.conv1 = GATConv(
            in_channels,
            hidden_channels,
            heads=4,
            dropout=0.2,
        )

        self.bn1 = BatchNorm(hidden_channels * 4)

        self.conv2 = GraphConv(
            hidden_channels * 4,
            hidden_channels * 2,
        )

        self.bn2 = BatchNorm(hidden_channels * 2)

        self.conv3 = GraphConv(
            hidden_channels * 2,
            hidden_channels,
        )

        self.bn3 = BatchNorm(hidden_channels)

        self.lin1 = torch.nn.Linear(hidden_channels, hidden_channels)

        self.lin2 = torch.nn.Linear(hidden_channels, num_classes)

        self.dropout = 0.4

    def forward(self, x, edge_index, batch):
        edge_index = knn_graph(
            x,
            k=6,
            loop=False,
        )

        # Layer 1
        x = self.conv1(x, edge_index)
        x = self.bn1(x)
        x = F.relu(x)

        # Layer 2
        x = self.conv2(x, edge_index)
        x = self.bn2(x)
        x = F.relu(x)

        # Layer 3
        x = self.conv3(x, edge_index)
        x = self.bn3(x)
        x = F.relu(x)

        # Pooling
        x = global_mean_pool(x, batch)

        # Classifier
        x = F.dropout(
            x,
            p=self.dropout,
            training=self.training,
        )

        x = self.lin1(x)
        x = F.relu(x)

        x = self.lin2(x)

        return x

# =========================================================
# DEVICE
# =========================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

sample = dataset[0]

model = DragonflyGNN(
    in_channels=sample.x.shape[1],
    hidden_channels=64,
    num_classes=num_classes,
).to(device)

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=1e-3,
    weight_decay=1e-4,
)

scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer,
    mode="max",
    patience=10,
)

criterion = torch.nn.CrossEntropyLoss()

# =========================================================
# TRAIN
# =========================================================

def train():

    model.train()

    total_loss = 0

    for data in train_loader:

        data = data.to(device)

        optimizer.zero_grad()

        out = model(
            data.x,
            data.edge_index,
            data.batch,
        )

        loss = criterion(
            out,
            data.y.view(-1),
        )

        loss.backward()

        torch.nn.utils.clip_grad_norm_(
            model.parameters(),
            2.0,
        )

        optimizer.step()

        total_loss += (
            loss.item() * data.num_graphs
        )

    return total_loss / len(train_loader)

# =========================================================
# EVAL
# =========================================================

@torch.no_grad()
def evaluate(loader):

    model.eval()

    correct = 0
    total = 0

    for data in loader:

        data = data.to(device)
        
        out = model(
            data.x,
            data.edge_index,
            data.batch,
        )

        pred = out.argmax(dim=1)

        correct += (
            pred == data.y.view(-1)
        ).sum().item()

        total += data.num_graphs

    return correct / total

# =========================================================
# TRAIN LOOP
# =========================================================

history = {
    "train_acc": [],
    "test_acc": [],
    "loss": [],
}

best_acc = 0

print(f"Training on {device}")

for epoch in range(1, 201):

    loss = train()

    train_acc = evaluate(train_loader)
    test_acc = evaluate(test_loader)

    scheduler.step(test_acc)

    history["loss"].append(loss)
    history["train_acc"].append(train_acc)
    history["test_acc"].append(test_acc)

    if test_acc > best_acc:

        best_acc = test_acc

        torch.save(
            model.state_dict(),
            "./best_dragonfly_model.pth",
        )

    print(
        f"Epoch {epoch:03d} | "
        f"Loss {loss:.4f} | "
        f"Train {train_acc:.4f} | "
        f"Test {test_acc:.4f}"
    )

print(f"\nBest Test Accuracy: {best_acc:.4f}")