"""
Random Forest Model for Perishable Goods Demand Forecasting
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV
import joblib
import os
import logging
import time
from typing import Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RandomForestForecaster:
    """Random Forest model for demand forecasting in hybrid architecture."""
    
    DEFAULT_PARAMS = {
        "n_estimators": 500, "max_depth": 20, "min_samples_split": 10,
        "min_samples_leaf": 5, "max_features": "sqrt", "n_jobs": -1,
        "random_state": 42, "verbose": 0,
    }
    
    TUNING_GRID = {
        "n_estimators": [200, 500], "max_depth": [15, 20, None],
        "min_samples_split": [5, 10], "min_samples_leaf": [3, 5],
    }
    
    def __init__(self, params: Dict = None):
        self.params = {**self.DEFAULT_PARAMS, **(params or {})}
        self.model = RandomForestRegressor(**self.params)
        self.feature_importances_ = None
        self.training_metrics_ = {}
        self.is_trained = False
    
    def train(self, X_train, y_train, feature_names=None):
        logger.info(f"Training RF on {X_train.shape[0]:,} samples, {X_train.shape[1]} features...")
        start = time.time()
        self.model.fit(X_train, y_train)
        elapsed = time.time() - start
        
        if feature_names:
            self.feature_importances_ = pd.Series(
                self.model.feature_importances_, index=feature_names
            ).sort_values(ascending=False)
        
        y_pred = self.model.predict(X_train)
        self.training_metrics_ = {
            "training_time_seconds": elapsed, "n_samples": X_train.shape[0],
            "train_mae": float(np.mean(np.abs(y_train - y_pred))),
            "train_rmse": float(np.sqrt(np.mean((y_train - y_pred) ** 2))),
            "train_mape": float(np.mean(np.abs((y_train - y_pred) / np.maximum(y_train, 1))) * 100),
        }
        self.is_trained = True
        logger.info(f"RF trained in {elapsed:.1f}s | MAE={self.training_metrics_['train_mae']:.2f}")
        return self.training_metrics_
    
    def predict(self, X):
        if not self.is_trained:
            raise RuntimeError("Model must be trained first.")
        return self.model.predict(X)
    
    def tune(self, X_train, y_train, param_grid=None, cv=3):
        param_grid = param_grid or self.TUNING_GRID
        logger.info("Tuning RF hyperparameters...")
        gs = GridSearchCV(RandomForestRegressor(random_state=42), param_grid,
                         cv=cv, scoring="neg_mean_absolute_error", n_jobs=-1, verbose=1, refit=True)
        gs.fit(X_train, y_train)
        self.model = gs.best_estimator_
        self.params = gs.best_params_
        logger.info(f"Best RF params: {gs.best_params_}, score={gs.best_score_:.4f}")
        return {"best_params": gs.best_params_, "best_score": float(gs.best_score_)}
    
    def get_feature_importances(self, top_n=20):
        if self.feature_importances_ is None:
            raise RuntimeError("Train with feature_names first.")
        return self.feature_importances_.head(top_n)
    
    def save(self, path="ml/artifacts/rf_model.joblib"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({"model": self.model, "params": self.params,
                     "importances": self.feature_importances_,
                     "metrics": self.training_metrics_, "is_trained": self.is_trained}, path)
        logger.info(f"Saved RF model to {path}")
    
    def load(self, path="ml/artifacts/rf_model.joblib"):
        data = joblib.load(path)
        self.model, self.params = data["model"], data["params"]
        self.feature_importances_ = data["importances"]
        self.training_metrics_ = data["metrics"]
        self.is_trained = data["is_trained"]
        logger.info(f"Loaded RF model from {path}")
