"""Module for pre-training a reward model from trajectory data (observations and rewards)."""
import math
import pickle
from os import path
from pathlib import Path

import numpy as np
import torch
import torch.optim as optim
from network import Network
from torch.nn import MSELoss
from torch.utils.data import DataLoader, Dataset, random_split


class TrajectoryDataset(Dataset):
    """PyTorch Dataset for loading trajectories data."""

    def __init__(self, file_path):
        """Initialize dataset."""
        with open(file_path, "rb") as handle:
            self.trajectories = pickle.load(handle)
        self.X = [t["obs"] for t in self.trajectories]
        self.y = [t["reward"] for t in self.trajectories]

    def __len__(self):
        """Return size of dataset."""
        return len(self.X)

    def __getitem__(self, idx):
        """Return item with given index."""
        return self.X[idx], self.y[idx]


def train_reward_model(
    reward_model: Network,
    dataset: Dataset,
    epochs: int,
    batch_size: int,
    split_ratio: float = 0.8,
    patience: int = 10,
):
    """Train a reward model given trajectories data."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    reward_model = reward_model.to(device)
    optimizer = optim.Adam(reward_model.parameters(), lr=1e-3)

    train_size = math.floor(split_ratio * len(dataset))
    train_set, val_set = random_split(
        dataset, lengths=[train_size, len(dataset) - train_size]
    )

    train_loader = DataLoader(
        train_set, batch_size=batch_size, shuffle=True, pin_memory=True
    )
    val_loader = DataLoader(
        val_set, batch_size=batch_size, shuffle=True, pin_memory=True
    )

    best_val_loss = float("inf")
    no_improvement_epochs = 0

    loss_fn = MSELoss(reduction="sum")

    best_model_state = reward_model.state_dict()  # Initialize with the initial state
    for epoch in range(epochs):
        # Training
        train_losses = []
        for obs, reward in train_loader:
            loss = loss_fn(reward_model(obs.float()), reward.float().unsqueeze(1))
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            train_losses.append(loss.item())
        avg_train_loss = np.mean(train_losses)

        # Validation
        with torch.no_grad():
            val_losses = []
            for obs, reward in val_loader:
                loss = loss_fn(reward_model(obs.float()), reward.float().unsqueeze(1))
                val_losses.append(loss.item())
            avg_val_loss = np.mean(val_losses)

        print(
            f"Epoch {epoch + 1}/{epochs}, Train Loss: {avg_train_loss}, Val Loss: {avg_val_loss}"
        )

        # Early stopping
        delta = 0.001  # minimum acceptable improvement
        if avg_val_loss < best_val_loss - delta:
            best_val_loss = avg_val_loss
            best_model_state = (
                reward_model.state_dict()
            )  # save the parameters of the best model
            current_path = Path(__file__).parent.resolve()
            torch.save(
                best_model_state,
                path.join(current_path, "models", "reward_model_pretrained.pth"),
            )  # save the parameters for later use to disk
            no_improvement_epochs = 0
        else:
            no_improvement_epochs += 1
            if no_improvement_epochs >= patience:
                print(
                    f"No improvement after for {patience} epochs, therefore stopping training."
                )
                break  # break instead of return, so that the function can return the best model state

    # load the weights and biases for the best model state during training
    reward_model.load_state_dict(best_model_state)

    return reward_model


def main():
    """Run reward model pre-training."""
    # File paths
    current_path = Path(__file__).parent.resolve()
    folder_path = path.join(current_path, "../rl/reward_data")
    file_path = path.join(folder_path, "ppo_HalfCheetah-v3_obs_reward_dataset.pkl")

    # Load data
    dataset = TrajectoryDataset(file_path)

    # Initialize network
    reward_model = Network(layer_num=3, input_dim=17, hidden_dim=256, output_dim=1)

    # Train model
    train_reward_model(reward_model, dataset, epochs=100, batch_size=32)


if __name__ == "__main__":
    main()
