# so we dont need this at all im just leaving it here for future reference










"""
pace_regressor.py

A tiny ML regressor for the pace metric.

This class does:
    - store training data
    - train a small linear model (or MLP)
    - save/load weights
    - predict a continuous pace_score ∈ [0,1]

It is intentionally simple so you can:
    - replace it later with a better model
    - or generate training data easily
"""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import json
from pathlib import Path
from typing import Dict, Any, Optional


# ----------------------------
# Model class
# ----------------------------

@dataclass
class PaceRegressorConfig:
    input_dim: int = 4       # number of features
    hidden_dim: int = 8      # small MLP layer
    learning_rate: float = 0.01
    max_iters: int = 5000


class PaceRegressor:
    """
    A micro neural-network:
        input → hidden (ReLU) → output (sigmoid)

    output ∈ [0,1] representing:
        slow (0) → optimal (~0.5) → fast (1)
    """

    def __init__(self, config: PaceRegressorConfig):
        self.cfg = config

        # Xavier init
        self.W1 = np.random.randn(config.input_dim, config.hidden_dim) * np.sqrt(2/config.input_dim)
        self.b1 = np.zeros(config.hidden_dim)

        self.W2 = np.random.randn(config.hidden_dim, 1) * np.sqrt(2/config.hidden_dim)
        self.b2 = np.zeros(1)

    # ----------------------------
    # Forward pass
    # ----------------------------
    def _relu(self, x):
        return np.maximum(0, x)

    def _sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

    def forward(self, X: np.ndarray):
        z1 = X @ self.W1 + self.b1
        h1 = self._relu(z1)
        z2 = h1 @ self.W2 + self.b2
        out = self._sigmoid(z2)
        return out, (z1, h1, z2)

    # ----------------------------
    # Backpropagation + SGD
    # ----------------------------
    def train(self, X: np.ndarray, y: np.ndarray):
        lr = self.cfg.learning_rate

        for _ in range(self.cfg.max_iters):
            out, (z1, h1, z2) = self.forward(X)

            # loss = MSE
            loss_grad = 2 * (out - y) / len(y)

            # backprop
            d_z2 = loss_grad * out * (1 - out)
            d_W2 = h1.T @ d_z2
            d_b2 = np.sum(d_z2, axis=0)

            d_h1 = d_z2 @ self.W2.T
            d_z1 = d_h1 * (z1 > 0)

            d_W1 = X.T @ d_z1
            d_b1 = np.sum(d_z1, axis=0)

            # parameter update
            self.W1 -= lr * d_W1
            self.b1 -= lr * d_b1
            self.W2 -= lr * d_W2
            self.b2 -= lr * d_b2

    # ----------------------------
    # Save / Load
    # ----------------------------
    def save(self, path: Path):
        data = {
            "W1": self.W1.tolist(),
            "b1": self.b1.tolist(),
            "W2": self.W2.tolist(),
            "b2": self.b2.tolist(),
        }
        path.write_text(json.dumps(data))

    @classmethod
    def load(cls, path: Path, config: PaceRegressorConfig):
        obj = cls(config)
        data = json.loads(path.read_text())
        obj.W1 = np.array(data["W1"])
        obj.b1 = np.array(data["b1"])
        obj.W2 = np.array(data["W2"])
        obj.b2 = np.array(data["b2"])
        return obj

    # ----------------------------
    # Predict
    # ----------------------------
    def predict(self, features: Dict[str, float]) -> float:
        """
        features = {
            'overall_wpm': ...,
            'mean_pause': ...,
            'pause_ratio': ...,
            'speech_ratio': ...
        }
        """
        X = np.array([
            features["overall_wpm"] / 300.0,     # normalize
            features["mean_pause"] / 2.0,
            features["pause_ratio"],
            features["speech_ratio"],
        ], dtype=float).reshape(1, -1)

        out, _ = self.forward(X)
        return float(out[0, 0])
