"""
LSTM Model (PyTorch) for Perishable Goods Demand Forecasting
Captures temporal dependencies and sequential patterns.
"""
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import os
import logging
import time
from typing import Dict, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TimeSeriesDataset(Dataset):
    """PyTorch Dataset for time series sequences."""
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)
    def __len__(self):
        return len(self.X)
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


class LSTMModel(nn.Module):
    """
    Multi-layer LSTM network for time series forecasting.
    Architecture: LSTM layers → Dropout → Fully connected → Output
    """
    def __init__(self, input_size, hidden_size=128, num_layers=2, dropout=0.2):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers,
                           batch_first=True, dropout=dropout if num_layers > 1 else 0)
        self.dropout = nn.Dropout(dropout)
        self.fc1 = nn.Linear(hidden_size, hidden_size // 2)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_size // 2, 1)
    
    def forward(self, x):
        # x: (batch, seq_len, features)
        lstm_out, _ = self.lstm(x)
        out = lstm_out[:, -1, :]  # Take last time step
        out = self.dropout(out)
        out = self.relu(self.fc1(out))
        out = self.fc2(out)
        return out.squeeze(-1)


class LSTMForecaster:
    """
    LSTM forecaster with training loop, early stopping, checkpointing,
    and learning rate scheduling.
    """
    def __init__(self, input_size, hidden_size=128, num_layers=2,
                 dropout=0.2, learning_rate=0.001, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = LSTMModel(input_size, hidden_size, num_layers, dropout).to(self.device)
        self.learning_rate = learning_rate
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='min', factor=0.5, patience=5)
        self.criterion = nn.MSELoss()
        self.training_history = []
        self.best_val_loss = float('inf')
        self.is_trained = False
        logger.info(f"LSTM on device: {self.device}, params: {sum(p.numel() for p in self.model.parameters()):,}")
    
    def train(self, X_train, y_train, X_val=None, y_val=None,
              epochs=50, batch_size=256, patience=10, checkpoint_dir="ml/artifacts"):
        """Train LSTM with early stopping and checkpointing."""
        train_ds = TimeSeriesDataset(X_train, y_train)
        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
        
        val_loader = None
        if X_val is not None:
            val_ds = TimeSeriesDataset(X_val, y_val)
            val_loader = DataLoader(val_ds, batch_size=batch_size)
        
        os.makedirs(checkpoint_dir, exist_ok=True)
        best_path = os.path.join(checkpoint_dir, "lstm_best.pt")
        patience_counter = 0
        start = time.time()
        
        logger.info(f"Training LSTM: {epochs} epochs, batch_size={batch_size}")
        
        for epoch in range(epochs):
            # Training phase
            self.model.train()
            train_loss = 0
            for X_batch, y_batch in train_loader:
                X_batch, y_batch = X_batch.to(self.device), y_batch.to(self.device)
                self.optimizer.zero_grad()
                pred = self.model(X_batch)
                loss = self.criterion(pred, y_batch)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                self.optimizer.step()
                train_loss += loss.item() * len(X_batch)
            train_loss /= len(train_ds)
            
            # Validation phase
            val_loss = None
            if val_loader:
                self.model.eval()
                val_total = 0
                with torch.no_grad():
                    for X_b, y_b in val_loader:
                        X_b, y_b = X_b.to(self.device), y_b.to(self.device)
                        pred = self.model(X_b)
                        val_total += self.criterion(pred, y_b).item() * len(X_b)
                val_loss = val_total / len(val_ds)
                self.scheduler.step(val_loss)
                
                if val_loss < self.best_val_loss:
                    self.best_val_loss = val_loss
                    torch.save(self.model.state_dict(), best_path)
                    patience_counter = 0
                else:
                    patience_counter += 1
            
            record = {"epoch": epoch + 1, "train_loss": train_loss, "val_loss": val_loss}
            self.training_history.append(record)
            
            if (epoch + 1) % 5 == 0 or epoch == 0:
                msg = f"Epoch {epoch+1}/{epochs} | Train Loss: {train_loss:.6f}"
                if val_loss: msg += f" | Val Loss: {val_loss:.6f}"
                logger.info(msg)
            
            if patience_counter >= patience:
                logger.info(f"Early stopping at epoch {epoch+1}")
                break
        
        # Load best model
        if os.path.exists(best_path):
            self.model.load_state_dict(torch.load(best_path, weights_only=True))
        
        self.is_trained = True
        elapsed = time.time() - start
        logger.info(f"LSTM training complete in {elapsed:.1f}s, best val_loss={self.best_val_loss:.6f}")
        return {"training_time": elapsed, "best_val_loss": self.best_val_loss,
                "epochs_trained": len(self.training_history)}
    
    def predict(self, X):
        """Generate predictions from sequences."""
        if not self.is_trained:
            raise RuntimeError("Model must be trained first.")
        self.model.eval()
        ds = TimeSeriesDataset(X, np.zeros(len(X)))
        loader = DataLoader(ds, batch_size=512)
        preds = []
        with torch.no_grad():
            for X_b, _ in loader:
                X_b = X_b.to(self.device)
                preds.append(self.model(X_b).cpu().numpy())
        return np.concatenate(preds)
    
    def save(self, path="ml/artifacts/lstm_model.pt"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save({
            "model_state": self.model.state_dict(),
            "config": {"input_size": self.model.lstm.input_size,
                       "hidden_size": self.model.hidden_size,
                       "num_layers": self.model.num_layers},
            "history": self.training_history,
            "best_val_loss": self.best_val_loss,
        }, path)
        logger.info(f"Saved LSTM model to {path}")
    
    def load(self, path="ml/artifacts/lstm_model.pt"):
        ckpt = torch.load(path, map_location=self.device, weights_only=False)
        cfg = ckpt["config"]
        self.model = LSTMModel(cfg["input_size"], cfg["hidden_size"], cfg["num_layers"]).to(self.device)
        self.model.load_state_dict(ckpt["model_state"])
        self.training_history = ckpt["history"]
        self.best_val_loss = ckpt["best_val_loss"]
        self.is_trained = True
        logger.info(f"Loaded LSTM model from {path}")
