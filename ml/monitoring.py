"""
Monitoring & Analytics Module

Provides: performance tracking by SKU/Store/Category,
holiday analysis, alert generation, and visualization data.
"""
import numpy as np
import pandas as pd
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

from ml.evaluate import Evaluator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ForecastMonitor:
    """Monitor forecast performance and detect anomalies."""
    
    def __init__(self, mape_threshold=30.0, spike_threshold=2.5):
        self.mape_threshold = mape_threshold
        self.spike_threshold = spike_threshold
        self.alerts = []
        self.performance_history = []
    
    def analyze_performance(self, df, y_true_col="actual", y_pred_col="predicted"):
        """Comprehensive performance analysis by dimensions."""
        results = {}
        
        # Overall
        results["overall"] = Evaluator.compute_metrics(df[y_true_col], df[y_pred_col])
        
        # By category
        if "category" in df.columns:
            results["by_category"] = Evaluator.compute_metrics_by_group(
                df, y_true_col, y_pred_col, "category").to_dict("records")
        
        # By store
        if "store_id" in df.columns:
            results["by_store"] = Evaluator.compute_metrics_by_group(
                df, y_true_col, y_pred_col, "store_id").to_dict("records")
        
        # By SKU (top worst performers)
        if "sku" in df.columns:
            by_sku = Evaluator.compute_metrics_by_group(df, y_true_col, y_pred_col, "sku")
            results["worst_skus"] = by_sku.tail(10).to_dict("records")
            results["best_skus"] = by_sku.head(10).to_dict("records")
        
        # Holiday analysis
        if "is_holiday" in df.columns:
            holiday_df = df[df["is_holiday"] == 1]
            non_holiday_df = df[df["is_holiday"] == 0]
            if len(holiday_df) > 0:
                results["holiday_performance"] = Evaluator.compute_metrics(
                    holiday_df[y_true_col], holiday_df[y_pred_col])
                results["non_holiday_performance"] = Evaluator.compute_metrics(
                    non_holiday_df[y_true_col], non_holiday_df[y_pred_col])
        
        # Error distribution
        results["error_distribution"] = Evaluator.error_distribution(df[y_true_col], df[y_pred_col])
        
        self.performance_history.append({
            "timestamp": datetime.now().isoformat(),
            "overall": results["overall"]
        })
        
        return results
    
    def check_alerts(self, df, y_true_col="actual", y_pred_col="predicted") -> List[Dict]:
        """Check for alert conditions."""
        alerts = []
        
        # High error alert
        errors = np.abs(df[y_true_col] - df[y_pred_col])
        mean_error = errors.mean()
        high_error_mask = errors > self.mape_threshold
        
        if high_error_mask.any():
            n_high = high_error_mask.sum()
            alerts.append({
                "type": "HIGH_ERROR", "severity": "WARNING",
                "message": f"{n_high} predictions exceeded error threshold ({self.mape_threshold})",
                "timestamp": datetime.now().isoformat(),
            })
        
        # Demand spike detection
        if "sales" in df.columns:
            rolling_mean = df.groupby(["store_id", "sku"])["sales"].transform(
                lambda x: x.rolling(7, min_periods=1).mean())
            rolling_std = df.groupby(["store_id", "sku"])["sales"].transform(
                lambda x: x.rolling(7, min_periods=1).std())
            spikes = df["sales"] > (rolling_mean + self.spike_threshold * rolling_std.fillna(1))
            
            if spikes.any():
                n_spikes = spikes.sum()
                alerts.append({
                    "type": "DEMAND_SPIKE", "severity": "INFO",
                    "message": f"{n_spikes} demand spikes detected",
                    "timestamp": datetime.now().isoformat(),
                })
        
        self.alerts.extend(alerts)
        return alerts
    
    def get_visualization_data(self, df, y_true_col="actual", y_pred_col="predicted"):
        """Prepare data for frontend visualization."""
        viz = {}
        
        # Time series overlay (aggregated by date)
        if "date" in df.columns:
            daily = df.groupby("date").agg({
                y_true_col: "mean", y_pred_col: "mean"
            }).reset_index()
            daily.columns = ["date", "actual", "predicted"]
            daily["date"] = daily["date"].astype(str)
            viz["time_series"] = daily.to_dict("records")
        
        # Residuals
        residuals = (df[y_true_col] - df[y_pred_col]).values
        viz["residual_histogram"] = {
            "values": np.histogram(residuals, bins=50)[0].tolist(),
            "bins": np.histogram(residuals, bins=50)[1].tolist(),
        }
        
        return viz
    
    def save_report(self, results, path="ml/artifacts/monitoring_report.json"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Monitoring report saved to {path}")
