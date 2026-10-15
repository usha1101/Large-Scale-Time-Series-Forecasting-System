"""
Evaluation Module: Metrics computation and performance analysis.
"""
import numpy as np
import pandas as pd
import json
import os
import logging
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Evaluator:
    """Compute and track forecasting evaluation metrics."""
    
    @staticmethod
    def compute_metrics(y_true, y_pred) -> Dict[str, float]:
        """
        Compute all evaluation metrics.
        Returns dict with MAE, RMSE, MAPE, SMAPE, R², MedAE.
        """
        y_true, y_pred = np.array(y_true, dtype=float), np.array(y_pred, dtype=float)
        mask = ~(np.isnan(y_true) | np.isnan(y_pred))
        y_true, y_pred = y_true[mask], y_pred[mask]
        
        errors = y_true - y_pred
        abs_errors = np.abs(errors)
        
        mae = float(np.mean(abs_errors))
        rmse = float(np.sqrt(np.mean(errors ** 2)))
        
        # MAPE (avoid division by zero)
        denom = np.maximum(np.abs(y_true), 1.0)
        mape = float(np.mean(abs_errors / denom) * 100)
        
        # SMAPE
        smape = float(np.mean(2 * abs_errors / (np.abs(y_true) + np.abs(y_pred) + 1e-8)) * 100)
        
        # R²
        ss_res = np.sum(errors ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = float(1 - ss_res / max(ss_tot, 1e-8))
        
        # Median Absolute Error
        medae = float(np.median(abs_errors))
        
        return {"mae": mae, "rmse": rmse, "mape": mape, "smape": smape, "r2": r2, "medae": medae}
    
    @staticmethod
    def compute_metrics_by_group(df, y_true_col, y_pred_col, group_col) -> pd.DataFrame:
        """Compute metrics grouped by category/store/SKU."""
        results = []
        for name, group in df.groupby(group_col):
            m = Evaluator.compute_metrics(group[y_true_col], group[y_pred_col])
            m[group_col] = name
            m["n_samples"] = len(group)
            results.append(m)
        return pd.DataFrame(results).sort_values("mape")
    
    @staticmethod
    def error_distribution(y_true, y_pred) -> Dict:
        """Analyze error distribution."""
        errors = np.array(y_true) - np.array(y_pred)
        return {
            "mean_error": float(np.mean(errors)),
            "std_error": float(np.std(errors)),
            "skewness": float(pd.Series(errors).skew()),
            "kurtosis": float(pd.Series(errors).kurtosis()),
            "p5": float(np.percentile(errors, 5)),
            "p25": float(np.percentile(errors, 25)),
            "p50": float(np.percentile(errors, 50)),
            "p75": float(np.percentile(errors, 75)),
            "p95": float(np.percentile(errors, 95)),
        }
    
    @staticmethod
    def save_results(results: Dict, path: str = "ml/artifacts/evaluation_results.json"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Saved evaluation results to {path}")
