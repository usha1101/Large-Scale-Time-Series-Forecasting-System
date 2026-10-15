"""
End-to-end Training Pipeline

Orchestrates: data loading → preprocessing → model training → evaluation → saving
Trains RF, LSTM, and Hybrid models with proper time-based splits.
"""
import numpy as np
import pandas as pd
import os
import json
import logging
import time
from datetime import datetime

from ml.preprocessing import PreprocessingPipeline, build_lstm_sequences, get_group_indices
from ml.models.random_forest import RandomForestForecaster
from ml.models.lstm import LSTMForecaster
from ml.models.hybrid import HybridForecaster
from ml.evaluate import Evaluator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ARTIFACTS_DIR = "ml/artifacts"
SEQ_LENGTH = 14


def load_data(data_path="data/sales_data.csv"):
    """Load and validate sales data."""
    logger.info(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    df["date"] = pd.to_datetime(df["date"])
    logger.info(f"Loaded {len(df):,} records, {df['sku'].nunique()} SKUs, {df['store_id'].nunique()} stores")
    return df


def train_pipeline(
    data_path="data/sales_data.csv",
    train_end="2024-06-30",
    val_end="2024-12-31",
    rf_params=None,
    lstm_epochs=30,
    lstm_hidden=128,
    lstm_layers=2,
    hybrid_strategy="stacking",
    sample_frac=None,
    artifacts_dir=ARTIFACTS_DIR,
):
    """
    Run the full training pipeline.
    
    Args:
        data_path: Path to sales CSV
        train_end: Training cutoff date
        val_end: Validation cutoff date
        rf_params: RF hyperparameters (None = defaults)
        lstm_epochs: Number of LSTM training epochs
        lstm_hidden: LSTM hidden size
        lstm_layers: Number of LSTM layers
        hybrid_strategy: 'stacking', 'weighted_avg', or 'rf_feature'
        sample_frac: Fraction of SKU-store combos to sample (for faster dev)
        artifacts_dir: Where to save models and artifacts
    """
    os.makedirs(artifacts_dir, exist_ok=True)
    run_start = time.time()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # ---- 1. Load Data ----
    df = load_data(data_path)
    
    if sample_frac and sample_frac < 1.0:
        combos = df.groupby(["store_id", "sku"]).ngroups
        sample_combos = df.groupby(["store_id", "sku"]).ngroup()
        n_keep = int(combos * sample_frac)
        keep_ids = np.random.choice(combos, n_keep, replace=False)
        df = df[sample_combos.isin(keep_ids)].reset_index(drop=True)
        logger.info(f"Sampled {n_keep}/{combos} SKU-store combos ({len(df):,} records)")
    
    # ---- 2. Preprocess ----
    pipeline = PreprocessingPipeline(artifacts_dir=artifacts_dir)
    df = pipeline.fit_transform(df)
    train_df, val_df, test_df = pipeline.time_based_split(df, train_end, val_end)
    
    # ---- 3. Prepare RF Data ----
    X_train_rf, y_train_rf, train_clean = pipeline.get_features_and_target(train_df, "standard")
    X_val_rf, y_val_rf, val_clean = pipeline.get_features_and_target(val_df, "standard")
    X_test_rf, y_test_rf, test_clean = pipeline.get_features_and_target(test_df, "standard")
    
    feature_names = pipeline.available_features_
    logger.info(f"RF data: train={X_train_rf.shape}, val={X_val_rf.shape}, test={X_test_rf.shape}")
    
    # ---- 4. Train Random Forest ----
    rf = RandomForestForecaster(rf_params)
    rf.train(X_train_rf, y_train_rf, feature_names)
    rf_pred_train = rf.predict(X_train_rf)
    rf_pred_val = rf.predict(X_val_rf)
    rf_pred_test = rf.predict(X_test_rf)
    rf.save(os.path.join(artifacts_dir, "rf_model.joblib"))
    
    # ---- 5. Prepare LSTM Data ----
    X_train_lstm, y_train_lstm, _ = pipeline.get_features_and_target(train_df, "minmax", True)
    X_val_lstm, y_val_lstm, _ = pipeline.get_features_and_target(val_df, "minmax", True)
    X_test_lstm, y_test_lstm, _ = pipeline.get_features_and_target(test_df, "minmax", True)
    
    # Build sequences (simple sequential for efficiency)
    X_train_seq, y_train_seq = build_lstm_sequences(X_train_lstm, y_train_lstm, SEQ_LENGTH)
    X_val_seq, y_val_seq = build_lstm_sequences(X_val_lstm, y_val_lstm, SEQ_LENGTH)
    X_test_seq, y_test_seq = build_lstm_sequences(X_test_lstm, y_test_lstm, SEQ_LENGTH)
    
    logger.info(f"LSTM sequences: train={X_train_seq.shape}, val={X_val_seq.shape}, test={X_test_seq.shape}")
    
    # ---- 6. Train LSTM ----
    n_features = X_train_seq.shape[2]
    lstm = LSTMForecaster(n_features, lstm_hidden, lstm_layers)
    lstm.train(X_train_seq, y_train_seq, X_val_seq, y_val_seq, epochs=lstm_epochs, checkpoint_dir=artifacts_dir)
    
    lstm_pred_train_scaled = lstm.predict(X_train_seq)
    lstm_pred_val_scaled = lstm.predict(X_val_seq)
    lstm_pred_test_scaled = lstm.predict(X_test_seq)
    
    # Inverse scale LSTM predictions
    lstm_pred_train = pipeline.inverse_scale_target(lstm_pred_train_scaled)
    lstm_pred_val = pipeline.inverse_scale_target(lstm_pred_val_scaled)
    lstm_pred_test = pipeline.inverse_scale_target(lstm_pred_test_scaled)
    y_train_lstm_inv = pipeline.inverse_scale_target(y_train_seq)
    y_val_lstm_inv = pipeline.inverse_scale_target(y_val_seq)
    y_test_lstm_inv = pipeline.inverse_scale_target(y_test_seq)
    
    lstm.save(os.path.join(artifacts_dir, "lstm_model.pt"))
    
    # ---- 7. Align predictions for Hybrid ----
    # RF and LSTM may have different sample counts due to sequence building
    # Use the minimum length
    min_train = min(len(rf_pred_train), len(lstm_pred_train))
    min_val = min(len(rf_pred_val), len(lstm_pred_val))
    min_test = min(len(rf_pred_test), len(lstm_pred_test))
    
    rf_tr, lstm_tr = rf_pred_train[-min_train:], lstm_pred_train[-min_train:]
    rf_v, lstm_v = rf_pred_val[-min_val:], lstm_pred_val[-min_val:]
    rf_te, lstm_te = rf_pred_test[-min_test:], lstm_pred_test[-min_test:]
    y_tr = y_train_rf[-min_train:]
    y_v = y_val_rf[-min_val:]
    y_te = y_test_rf[-min_test:]
    
    # ---- 8. Train Hybrid ----
    hybrid = HybridForecaster(strategy=hybrid_strategy)
    hybrid.train(rf_tr, lstm_tr, y_tr, rf_v, lstm_v, y_v)
    hybrid_pred_test = hybrid.predict(rf_te, lstm_te)
    hybrid.save(os.path.join(artifacts_dir, "hybrid_model.joblib"))
    
    # ---- 9. Evaluate ----
    evaluator = Evaluator()
    
    # Naive baseline (predict previous day)
    naive_pred = np.roll(y_te, 1)
    naive_pred[0] = y_te[0]
    
    results = {
        "random_forest": evaluator.compute_metrics(y_te, rf_te),
        "lstm": evaluator.compute_metrics(y_te[:min_test], lstm_te[:min_test]),
        "hybrid": evaluator.compute_metrics(y_te, hybrid_pred_test),
        "naive_baseline": evaluator.compute_metrics(y_te, naive_pred),
    }
    
    # Check MAPE improvement
    naive_mape = results["naive_baseline"]["mape"]
    hybrid_mape = results["hybrid"]["mape"]
    improvement = ((naive_mape - hybrid_mape) / naive_mape) * 100
    results["mape_improvement_over_naive"] = improvement
    
    logger.info("\n" + "="*60)
    logger.info("EVALUATION RESULTS (Test Set)")
    logger.info("="*60)
    for model_name, metrics in results.items():
        if isinstance(metrics, dict):
            logger.info(f"\n{model_name}:")
            for k, v in metrics.items():
                logger.info(f"  {k}: {v:.4f}")
    logger.info(f"\nMAPE improvement over naive: {improvement:.1f}%")
    logger.info("="*60)
    
    # ---- 10. Save Results ----
    pipeline.save(artifacts_dir)
    
    run_metadata = {
        "run_id": run_id, "data_path": data_path,
        "train_end": train_end, "val_end": val_end,
        "hybrid_strategy": hybrid_strategy, "lstm_epochs": lstm_epochs,
        "results": {k: v for k, v in results.items() if isinstance(v, dict)},
        "mape_improvement": improvement,
        "total_time_seconds": time.time() - run_start,
    }
    
    with open(os.path.join(artifacts_dir, "run_metadata.json"), "w") as f:
        json.dump(run_metadata, f, indent=2, default=str)
    
    logger.info(f"\nTotal pipeline time: {time.time() - run_start:.1f}s")
    logger.info(f"All artifacts saved to {artifacts_dir}/")
    
    return results


if __name__ == "__main__":
    # For development: sample 5% of combos for speed
    results = train_pipeline(
        sample_frac=0.05,
        lstm_epochs=15,
        hybrid_strategy="stacking",
    )
