"""
Hybrid Stacking Model: RF + LSTM → Meta-Learner

Integration Strategy: Ensemble Stacking (Option A - Recommended)
- Train RF and LSTM independently
- Use their outputs as features for a meta-model (XGBoost)
- Supports toggling between stacking, RF-as-feature, and weighted averaging

This module also supports:
  Option B: RF predictions as additional input features to LSTM
  Option C: Weighted averaging with learned weights
"""
import numpy as np
import xgboost as xgb
from sklearn.linear_model import Ridge
import joblib
import os
import logging
from typing import Dict, Literal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridForecaster:
    """
    Hybrid ensemble combining Random Forest and LSTM predictions.
    
    Strategies:
        'stacking': Meta-learner (XGBoost) on top of RF + LSTM outputs
        'weighted_avg': Learned weighted average of RF + LSTM
        'rf_feature': RF predictions fed as extra features to LSTM
    """
    
    def __init__(self, strategy: Literal["stacking", "weighted_avg", "rf_feature"] = "stacking"):
        self.strategy = strategy
        self.meta_model = None
        self.weights_ = None
        self.metrics_ = {}
        self.is_trained = False
        
        if strategy == "stacking":
            self.meta_model = xgb.XGBRegressor(
                n_estimators=200, max_depth=5, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8,
                random_state=42, n_jobs=-1,
            )
        elif strategy == "weighted_avg":
            self.meta_model = Ridge(alpha=1.0)
    
    def train(self, rf_preds_train, lstm_preds_train, y_train,
              rf_preds_val=None, lstm_preds_val=None, y_val=None):
        """
        Train the meta-learner on base model predictions.
        
        Args:
            rf_preds_train: RF predictions on training set
            lstm_preds_train: LSTM predictions on training set
            y_train: True targets for training
            rf_preds_val/lstm_preds_val/y_val: Optional validation data
        """
        logger.info(f"Training hybrid model (strategy={self.strategy})...")
        
        if self.strategy == "stacking":
            X_meta = np.column_stack([rf_preds_train, lstm_preds_train])
            eval_set = None
            if rf_preds_val is not None:
                X_meta_val = np.column_stack([rf_preds_val, lstm_preds_val])
                eval_set = [(X_meta_val, y_val)]
            
            self.meta_model.fit(X_meta, y_train, eval_set=eval_set, verbose=False)
            preds = self.meta_model.predict(X_meta)
            
        elif self.strategy == "weighted_avg":
            X_meta = np.column_stack([rf_preds_train, lstm_preds_train])
            self.meta_model.fit(X_meta, y_train)
            self.weights_ = self.meta_model.coef_
            preds = self.meta_model.predict(X_meta)
            logger.info(f"Learned weights: RF={self.weights_[0]:.3f}, LSTM={self.weights_[1]:.3f}")
            
        elif self.strategy == "rf_feature":
            # In this strategy, training happens outside - this is a pass-through
            preds = 0.5 * rf_preds_train + 0.5 * lstm_preds_train
        
        self.metrics_ = {
            "train_mae": float(np.mean(np.abs(y_train - preds))),
            "train_rmse": float(np.sqrt(np.mean((y_train - preds) ** 2))),
            "train_mape": float(np.mean(np.abs((y_train - preds) / np.maximum(y_train, 1))) * 100),
        }
        
        if rf_preds_val is not None:
            val_preds = self.predict(rf_preds_val, lstm_preds_val)
            self.metrics_["val_mae"] = float(np.mean(np.abs(y_val - val_preds)))
            self.metrics_["val_rmse"] = float(np.sqrt(np.mean((y_val - val_preds) ** 2)))
            self.metrics_["val_mape"] = float(
                np.mean(np.abs((y_val - val_preds) / np.maximum(y_val, 1))) * 100)
        
        self.is_trained = True
        logger.info(f"Hybrid metrics: {self.metrics_}")
        return self.metrics_
    
    def predict(self, rf_preds, lstm_preds):
        """Generate ensemble predictions."""
        if not self.is_trained:
            raise RuntimeError("Hybrid model must be trained first.")
        
        if self.strategy in ("stacking", "weighted_avg"):
            X_meta = np.column_stack([rf_preds, lstm_preds])
            return self.meta_model.predict(X_meta)
        else:
            return 0.5 * rf_preds + 0.5 * lstm_preds
    
    def save(self, path="ml/artifacts/hybrid_model.joblib"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({"strategy": self.strategy, "meta_model": self.meta_model,
                     "weights": self.weights_, "metrics": self.metrics_,
                     "is_trained": self.is_trained}, path)
        logger.info(f"Saved hybrid model to {path}")
    
    def load(self, path="ml/artifacts/hybrid_model.joblib"):
        data = joblib.load(path)
        self.strategy = data["strategy"]
        self.meta_model = data["meta_model"]
        self.weights_ = data["weights"]
        self.metrics_ = data["metrics"]
        self.is_trained = data["is_trained"]
        logger.info(f"Loaded hybrid model (strategy={self.strategy})")
