"""
Preprocessing Pipeline for Perishable Goods Forecasting

Handles:
- Missing value imputation (forward fill, interpolation, ML-based)
- Feature engineering (temporal, lag, rolling, categorical)
- Scaling (StandardScaler for RF, MinMaxScaler for LSTM)
- Time-based train/val/test splitting
- Pipeline serialization for production deployment
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
import joblib
import os
import logging
from typing import Tuple, Dict, Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================
# Custom Transformer: Missing Value Handler
# ============================================================
class MissingValueHandler(BaseEstimator, TransformerMixin):
    """
    Handle missing values in sales data using multiple strategies:
    - Forward fill within each SKU-store group
    - Linear interpolation for remaining gaps
    - Fallback to group median
    """
    
    def __init__(self, strategy: str = "ffill_interpolate", group_cols: List[str] = None):
        self.strategy = strategy
        self.group_cols = group_cols or ["store_id", "sku"]
        self.group_medians_ = {}
    
    def fit(self, X: pd.DataFrame, y=None):
        """Learn group medians for fallback imputation."""
        if "sales" in X.columns:
            for name, group in X.groupby(self.group_cols):
                self.group_medians_[name] = group["sales"].median()
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Apply imputation strategy."""
        X = X.copy()
        
        if "sales" not in X.columns:
            return X
        
        initial_missing = X["sales"].isna().sum()
        
        if self.strategy == "ffill_interpolate":
            # Step 1: Forward fill within groups
            X["sales"] = X.groupby(self.group_cols)["sales"].transform(
                lambda s: s.ffill()
            )
            # Step 2: Interpolate remaining
            X["sales"] = X.groupby(self.group_cols)["sales"].transform(
                lambda s: s.interpolate(method="linear", limit_direction="both")
            )
        elif self.strategy == "ffill":
            X["sales"] = X.groupby(self.group_cols)["sales"].transform(
                lambda s: s.ffill().bfill()
            )
        elif self.strategy == "interpolate":
            X["sales"] = X.groupby(self.group_cols)["sales"].transform(
                lambda s: s.interpolate(method="linear", limit_direction="both")
            )
        
        # Fallback: fill any remaining NaN with group median
        remaining = X["sales"].isna().sum()
        if remaining > 0:
            for name, group_idx in X.groupby(self.group_cols).groups.items():
                mask = X.loc[group_idx, "sales"].isna()
                if mask.any():
                    median = self.group_medians_.get(name, X["sales"].median())
                    X.loc[group_idx[mask], "sales"] = median
        
        # Final fallback: global median
        X["sales"].fillna(X["sales"].median(), inplace=True)
        
        final_missing = X["sales"].isna().sum()
        logger.info(f"Missing values: {initial_missing} → {final_missing}")
        
        return X


# ============================================================
# Custom Transformer: Feature Engineer
# ============================================================
class FeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Generate all features for the forecasting models:
    - Time-based: day_of_week, week_of_year, month, quarter, day_of_month
    - Lag features: t-1, t-7, t-14, t-21, t-28
    - Rolling statistics: 7-day and 14-day mean, std, min, max
    - Trend indicators: diff, pct_change
    - Holiday markers (already present in data)
    """
    
    def __init__(self, lag_days: List[int] = None, rolling_windows: List[int] = None):
        self.lag_days = lag_days or [1, 7, 14, 21, 28]
        self.rolling_windows = rolling_windows or [7, 14, 28]
    
    def fit(self, X: pd.DataFrame, y=None):
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        X["date"] = pd.to_datetime(X["date"])
        
        # --- Time-based features ---
        X["day_of_week"] = X["date"].dt.dayofweek
        X["day_of_month"] = X["date"].dt.day
        X["week_of_year"] = X["date"].dt.isocalendar().week.astype(int)
        X["month"] = X["date"].dt.month
        X["quarter"] = X["date"].dt.quarter
        X["day_of_year"] = X["date"].dt.dayofyear
        X["is_weekend"] = (X["day_of_week"] >= 5).astype(int)
        X["is_month_start"] = X["date"].dt.is_month_start.astype(int)
        X["is_month_end"] = X["date"].dt.is_month_end.astype(int)
        
        # --- Cyclical encoding for periodic features ---
        X["day_of_week_sin"] = np.sin(2 * np.pi * X["day_of_week"] / 7)
        X["day_of_week_cos"] = np.cos(2 * np.pi * X["day_of_week"] / 7)
        X["month_sin"] = np.sin(2 * np.pi * X["month"] / 12)
        X["month_cos"] = np.cos(2 * np.pi * X["month"] / 12)
        X["day_of_year_sin"] = np.sin(2 * np.pi * X["day_of_year"] / 365.25)
        X["day_of_year_cos"] = np.cos(2 * np.pi * X["day_of_year"] / 365.25)
        
        # --- Lag features (per SKU-store group) ---
        logger.info("Computing lag features...")
        group_cols = ["store_id", "sku"]
        for lag in self.lag_days:
            X[f"sales_lag_{lag}"] = X.groupby(group_cols)["sales"].shift(lag)
        
        # --- Rolling statistics ---
        logger.info("Computing rolling statistics...")
        for window in self.rolling_windows:
            rolled = X.groupby(group_cols)["sales"]
            X[f"sales_rolling_mean_{window}"] = rolled.transform(
                lambda s: s.shift(1).rolling(window, min_periods=1).mean()
            )
            X[f"sales_rolling_std_{window}"] = rolled.transform(
                lambda s: s.shift(1).rolling(window, min_periods=1).std()
            )
            X[f"sales_rolling_min_{window}"] = rolled.transform(
                lambda s: s.shift(1).rolling(window, min_periods=1).min()
            )
            X[f"sales_rolling_max_{window}"] = rolled.transform(
                lambda s: s.shift(1).rolling(window, min_periods=1).max()
            )
        
        # --- Trend indicators ---
        X["sales_diff_1"] = X.groupby(group_cols)["sales"].diff(1)
        X["sales_diff_7"] = X.groupby(group_cols)["sales"].diff(7)
        X["sales_pct_change_1"] = X.groupby(group_cols)["sales"].pct_change(1)
        X["sales_pct_change_7"] = X.groupby(group_cols)["sales"].pct_change(7)
        
        # --- Expanding mean (long-term average) ---
        X["sales_expanding_mean"] = X.groupby(group_cols)["sales"].transform(
            lambda s: s.shift(1).expanding(min_periods=1).mean()
        )
        
        # Replace infinities
        X.replace([np.inf, -np.inf], np.nan, inplace=True)
        
        return X


# ============================================================
# Custom Transformer: Categorical Encoder
# ============================================================
class CategoricalEncoder(BaseEstimator, TransformerMixin):
    """Encode categorical variables using LabelEncoder."""
    
    def __init__(self, columns: List[str] = None):
        self.columns = columns or ["store_id", "sku", "category", "store_region", "store_size"]
        self.encoders_ = {}
    
    def fit(self, X: pd.DataFrame, y=None):
        for col in self.columns:
            if col in X.columns:
                le = LabelEncoder()
                le.fit(X[col].astype(str))
                self.encoders_[col] = le
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        for col, le in self.encoders_.items():
            if col in X.columns:
                # Handle unseen labels
                X[f"{col}_encoded"] = X[col].astype(str).map(
                    lambda v: le.transform([v])[0] if v in le.classes_ else -1
                )
        return X


# ============================================================
# Main Preprocessing Pipeline
# ============================================================
class PreprocessingPipeline:
    """
    End-to-end preprocessing pipeline for the forecasting system.
    
    Pipeline steps:
    1. Missing value handling
    2. Feature engineering
    3. Categorical encoding
    4. Feature selection
    5. Scaling (separate scalers for RF and LSTM)
    
    Supports saving/loading all preprocessing artifacts.
    """
    
    # Features used by the models
    FEATURE_COLS = [
        # Time features
        "day_of_week", "day_of_month", "week_of_year", "month", "quarter",
        "is_weekend", "is_month_start", "is_month_end",
        "day_of_week_sin", "day_of_week_cos", "month_sin", "month_cos",
        "day_of_year_sin", "day_of_year_cos",
        # Lag features
        "sales_lag_1", "sales_lag_7", "sales_lag_14", "sales_lag_21", "sales_lag_28",
        # Rolling features
        "sales_rolling_mean_7", "sales_rolling_std_7",
        "sales_rolling_min_7", "sales_rolling_max_7",
        "sales_rolling_mean_14", "sales_rolling_std_14",
        "sales_rolling_min_14", "sales_rolling_max_14",
        "sales_rolling_mean_28", "sales_rolling_std_28",
        "sales_rolling_min_28", "sales_rolling_max_28",
        # Trend
        "sales_diff_1", "sales_diff_7",
        "sales_pct_change_1", "sales_pct_change_7",
        "sales_expanding_mean",
        # Context
        "is_promotion", "is_holiday", "is_pre_holiday", "is_post_holiday",
        "shelf_life_days", "price",
        # Encoded categoricals
        "store_id_encoded", "sku_encoded", "category_encoded",
        "store_region_encoded", "store_size_encoded",
    ]
    
    TARGET_COL = "sales"
    
    def __init__(self, artifacts_dir: str = "ml/artifacts"):
        self.artifacts_dir = artifacts_dir
        self.missing_handler = MissingValueHandler()
        self.feature_engineer = FeatureEngineer()
        self.cat_encoder = CategoricalEncoder()
        self.standard_scaler = StandardScaler()
        self.minmax_scaler = MinMaxScaler()
        self.target_scaler = MinMaxScaler()
        self.is_fitted = False
    
    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fit all transformers and transform data."""
        logger.info("Step 1/5: Handling missing values...")
        df = self.missing_handler.fit_transform(df)
        
        logger.info("Step 2/5: Engineering features...")
        df = self.feature_engineer.fit_transform(df)
        
        logger.info("Step 3/5: Encoding categoricals...")
        df = self.cat_encoder.fit_transform(df)
        
        logger.info("Step 4/5: Selecting features...")
        # Ensure all feature columns exist
        available_features = [c for c in self.FEATURE_COLS if c in df.columns]
        self.available_features_ = available_features
        
        logger.info("Step 5/5: Fitting scalers...")
        # Drop rows with NaN in features (from lag/rolling warmup)
        feature_mask = df[available_features + [self.TARGET_COL]].notna().all(axis=1)
        df_clean = df[feature_mask].copy()
        
        # Fit scalers on clean data
        self.standard_scaler.fit(df_clean[available_features])
        self.minmax_scaler.fit(df_clean[available_features])
        self.target_scaler.fit(df_clean[[self.TARGET_COL]])
        
        self.is_fitted = True
        logger.info(f"Pipeline fitted. Clean samples: {len(df_clean):,} / {len(df):,}")
        
        return df
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform data using fitted transformers."""
        if not self.is_fitted:
            raise RuntimeError("Pipeline must be fitted before transform.")
        
        df = self.missing_handler.transform(df)
        df = self.feature_engineer.transform(df)
        df = self.cat_encoder.transform(df)
        
        return df
    
    def get_features_and_target(
        self,
        df: pd.DataFrame,
        scaler_type: str = "standard",
        scale_target: bool = False
    ) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
        """
        Extract feature matrix and target vector from processed DataFrame.
        
        Args:
            df: Processed DataFrame
            scaler_type: 'standard' for RF, 'minmax' for LSTM
            scale_target: Whether to scale the target variable
        
        Returns:
            X: Feature matrix (n_samples, n_features)
            y: Target vector (n_samples,)
            df_clean: Cleaned DataFrame with metadata
        """
        features = self.available_features_
        
        # Drop NaN rows
        mask = df[features + [self.TARGET_COL]].notna().all(axis=1)
        df_clean = df[mask].copy()
        
        X = df_clean[features].values
        y = df_clean[self.TARGET_COL].values
        
        # Scale features
        if scaler_type == "standard":
            X = self.standard_scaler.transform(X)
        elif scaler_type == "minmax":
            X = self.minmax_scaler.transform(X)
        
        # Optionally scale target
        if scale_target:
            y = self.target_scaler.transform(y.reshape(-1, 1)).ravel()
        
        return X, y, df_clean
    
    def inverse_scale_target(self, y_scaled: np.ndarray) -> np.ndarray:
        """Inverse transform scaled target values."""
        return self.target_scaler.inverse_transform(y_scaled.reshape(-1, 1)).ravel()
    
    def time_based_split(
        self,
        df: pd.DataFrame,
        train_end: str = "2024-06-30",
        val_end: str = "2024-12-31"
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Strict time-based split ensuring no data leakage.
        
        Args:
            df: Full dataset with 'date' column
            train_end: Last date of training set (inclusive)
            val_end: Last date of validation set (inclusive)
        
        Returns:
            train_df, val_df, test_df
        """
        df["date"] = pd.to_datetime(df["date"])
        train_end = pd.to_datetime(train_end)
        val_end = pd.to_datetime(val_end)
        
        train_df = df[df["date"] <= train_end].copy()
        val_df = df[(df["date"] > train_end) & (df["date"] <= val_end)].copy()
        test_df = df[df["date"] > val_end].copy()
        
        logger.info(f"Split sizes - Train: {len(train_df):,}, Val: {len(val_df):,}, Test: {len(test_df):,}")
        logger.info(f"Train: ... - {train_end.date()}")
        logger.info(f"Val:   {(train_end + pd.Timedelta(days=1)).date()} - {val_end.date()}")
        logger.info(f"Test:  {(val_end + pd.Timedelta(days=1)).date()} - ...")
        
        return train_df, val_df, test_df
    
    def save(self, path: str = None):
        """Save all preprocessing artifacts to disk."""
        path = path or self.artifacts_dir
        os.makedirs(path, exist_ok=True)
        
        artifacts = {
            "missing_handler": self.missing_handler,
            "feature_engineer": self.feature_engineer,
            "cat_encoder": self.cat_encoder,
            "standard_scaler": self.standard_scaler,
            "minmax_scaler": self.minmax_scaler,
            "target_scaler": self.target_scaler,
            "available_features": self.available_features_,
            "is_fitted": self.is_fitted,
        }
        
        artifact_path = os.path.join(path, "preprocessing_pipeline.joblib")
        joblib.dump(artifacts, artifact_path)
        logger.info(f"Saved preprocessing artifacts to {artifact_path}")
    
    def load(self, path: str = None):
        """Load preprocessing artifacts from disk."""
        path = path or self.artifacts_dir
        artifact_path = os.path.join(path, "preprocessing_pipeline.joblib")
        
        artifacts = joblib.load(artifact_path)
        self.missing_handler = artifacts["missing_handler"]
        self.feature_engineer = artifacts["feature_engineer"]
        self.cat_encoder = artifacts["cat_encoder"]
        self.standard_scaler = artifacts["standard_scaler"]
        self.minmax_scaler = artifacts["minmax_scaler"]
        self.target_scaler = artifacts["target_scaler"]
        self.available_features_ = artifacts["available_features"]
        self.is_fitted = artifacts["is_fitted"]
        
        logger.info(f"Loaded preprocessing artifacts from {artifact_path}")


# ============================================================
# LSTM Sequence Builder
# ============================================================
def build_lstm_sequences(
    X: np.ndarray,
    y: np.ndarray,
    seq_length: int = 14,
    group_indices: Optional[Dict] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build sequences for LSTM input from flat feature matrix.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        seq_length: Number of time steps per sequence
        group_indices: Dict mapping group_key → list of indices
                      If None, builds sequences across the entire array
    
    Returns:
        X_seq: (n_sequences, seq_length, n_features)
        y_seq: (n_sequences,)
    """
    if group_indices is None:
        # Simple sequential building
        sequences_X, sequences_y = [], []
        for i in range(seq_length, len(X)):
            sequences_X.append(X[i - seq_length:i])
            sequences_y.append(y[i])
        return np.array(sequences_X), np.array(sequences_y)
    
    # Build sequences per group (respecting SKU-store boundaries)
    all_X, all_y = [], []
    for key, indices in group_indices.items():
        if len(indices) < seq_length + 1:
            continue
        X_group = X[indices]
        y_group = y[indices]
        for i in range(seq_length, len(X_group)):
            all_X.append(X_group[i - seq_length:i])
            all_y.append(y_group[i])
    
    return np.array(all_X), np.array(all_y)


def get_group_indices(df: pd.DataFrame, group_cols: List[str] = None) -> Dict:
    """Get index arrays for each SKU-store group."""
    group_cols = group_cols or ["store_id", "sku"]
    indices = {}
    for name, group in df.groupby(group_cols):
        indices[name] = group.index.tolist()
    return indices


if __name__ == "__main__":
    # Test the pipeline
    logger.info("Testing preprocessing pipeline...")
    
    # Load data
    df = pd.read_csv("data/sales_data.csv")
    logger.info(f"Loaded {len(df):,} records")
    
    # Initialize and run pipeline
    pipeline = PreprocessingPipeline()
    df_processed = pipeline.fit_transform(df)
    
    # Split
    train_df, val_df, test_df = pipeline.time_based_split(df_processed)
    
    # Get features for RF
    X_train, y_train, train_clean = pipeline.get_features_and_target(
        train_df, scaler_type="standard"
    )
    logger.info(f"RF features shape: {X_train.shape}")
    
    # Get features for LSTM
    X_train_lstm, y_train_lstm, _ = pipeline.get_features_and_target(
        train_df, scaler_type="minmax", scale_target=True
    )
    
    # Build sequences
    group_idx = get_group_indices(train_clean)
    X_seq, y_seq = build_lstm_sequences(X_train_lstm, y_train_lstm, seq_length=14, group_indices=group_idx)
    logger.info(f"LSTM sequences shape: {X_seq.shape}")
    
    # Save pipeline
    pipeline.save()
    logger.info("Pipeline test complete!")
