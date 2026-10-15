"""Unit tests for ML pipeline components."""
import numpy as np
import pandas as pd
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPreprocessing:
    """Test preprocessing pipeline."""
    
    def _make_sample_df(self, n=500):
        dates = pd.date_range("2024-01-01", periods=n, freq="D")
        return pd.DataFrame({
            "date": np.tile(dates[:50], 10),
            "store_id": np.repeat([f"store_{i:03d}" for i in range(10)], 50),
            "sku": np.repeat([f"dairy_milk_{i}" for i in range(10)], 50),
            "category": "dairy",
            "sales": np.random.exponential(50, n),
            "is_promotion": 0, "promotion_lift": 1.0,
            "is_holiday": 0, "is_pre_holiday": 0, "is_post_holiday": 0,
            "store_region": "northeast", "store_size": "medium",
            "shelf_life_days": 14, "price": 4.99,
        })
    
    def test_missing_value_handler(self):
        from ml.preprocessing import MissingValueHandler
        df = self._make_sample_df()
        df.loc[10:15, "sales"] = np.nan
        handler = MissingValueHandler()
        result = handler.fit_transform(df)
        assert result["sales"].isna().sum() == 0
    
    def test_feature_engineer(self):
        from ml.preprocessing import FeatureEngineer
        df = self._make_sample_df()
        eng = FeatureEngineer()
        result = eng.transform(df)
        assert "day_of_week" in result.columns
        assert "sales_lag_1" in result.columns
        assert "sales_rolling_mean_7" in result.columns
    
    def test_categorical_encoder(self):
        from ml.preprocessing import CategoricalEncoder
        df = self._make_sample_df()
        enc = CategoricalEncoder()
        result = enc.fit_transform(df)
        assert "store_id_encoded" in result.columns
        assert "sku_encoded" in result.columns
    
    def test_full_pipeline(self):
        from ml.preprocessing import PreprocessingPipeline
        df = self._make_sample_df()
        pipeline = PreprocessingPipeline()
        result = pipeline.fit_transform(df)
        assert pipeline.is_fitted
        assert len(pipeline.available_features_) > 0
    
    def test_time_split(self):
        from ml.preprocessing import PreprocessingPipeline
        df = self._make_sample_df()
        pipeline = PreprocessingPipeline()
        df = pipeline.fit_transform(df)
        train, val, test = pipeline.time_based_split(df, "2024-01-20", "2024-02-10")
        assert len(train) > 0


class TestModels:
    """Test model implementations."""
    
    def test_rf_train_predict(self):
        from ml.models.random_forest import RandomForestForecaster
        X = np.random.randn(1000, 10)
        y = np.random.exponential(50, 1000)
        rf = RandomForestForecaster({"n_estimators": 10, "max_depth": 5})
        rf.train(X, y)
        preds = rf.predict(X[:10])
        assert len(preds) == 10
        assert rf.is_trained
    
    def test_lstm_train_predict(self):
        from ml.models.lstm import LSTMForecaster
        X = np.random.randn(500, 14, 10)
        y = np.random.randn(500)
        lstm = LSTMForecaster(input_size=10, hidden_size=32, num_layers=1)
        lstm.train(X, y, epochs=2, batch_size=64)
        preds = lstm.predict(X[:10])
        assert len(preds) == 10
    
    def test_hybrid_stacking(self):
        from ml.models.hybrid import HybridForecaster
        rf_preds = np.random.randn(200) + 50
        lstm_preds = np.random.randn(200) + 50
        y_true = np.random.randn(200) + 50
        hybrid = HybridForecaster("stacking")
        hybrid.train(rf_preds, lstm_preds, y_true)
        preds = hybrid.predict(rf_preds[:10], lstm_preds[:10])
        assert len(preds) == 10
    
    def test_evaluate_metrics(self):
        from ml.evaluate import Evaluator
        y_true = np.array([10, 20, 30, 40, 50])
        y_pred = np.array([12, 18, 33, 38, 52])
        metrics = Evaluator.compute_metrics(y_true, y_pred)
        assert "mae" in metrics
        assert "rmse" in metrics
        assert "mape" in metrics
        assert metrics["mae"] > 0


class TestAPI:
    """Test FastAPI endpoints."""
    
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from backend.main import app
        with TestClient(app) as client:
            yield client
    
    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Forecasting" in resp.json()["message"]
    
    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
    
    def test_login(self, client):
        resp = client.post("/api/auth/login",
                          json={"username": "admin", "password": "admin123"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()
    
    def test_predict(self, client):
        resp = client.post("/api/predict", json={
            "sku": "dairy_whole_milk", "store_id": "store_001",
            "start_date": "2025-04-01", "end_date": "2025-04-07"
        })
        assert resp.status_code == 200
        assert len(resp.json()["forecasts"]) == 7
    
    def test_batch_predict(self, client):
        resp = client.post("/api/batch_predict", json={
            "predictions": [
                {"sku": "dairy_whole_milk", "store_id": "store_001",
                 "start_date": "2025-04-01", "end_date": "2025-04-03"},
                {"sku": "produce_bananas", "store_id": "store_002",
                 "start_date": "2025-04-01", "end_date": "2025-04-03"},
            ]
        })
        assert resp.status_code == 200
        assert resp.json()["total_forecasts"] == 6
    
    def test_metrics(self, client):
        resp = client.get("/api/metrics")
        assert resp.status_code == 200
        assert "metrics" in resp.json()
    
    def test_skus(self, client):
        resp = client.get("/api/metrics/skus")
        assert resp.status_code == 200
        assert len(resp.json()["skus"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
