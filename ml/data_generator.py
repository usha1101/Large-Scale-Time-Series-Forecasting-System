"""
Synthetic Data Generator for Perishable Goods Forecasting
Generates realistic sales data for 10,000+ SKU-store combinations
with seasonality, holidays, promotions, and demand volatility.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
PERISHABLE_CATEGORIES = {
    "dairy": {
        "skus": ["whole_milk", "skim_milk", "yogurt_plain", "yogurt_fruit",
                 "cheddar_cheese", "mozzarella", "cream_cheese", "butter",
                 "cottage_cheese", "sour_cream"],
        "base_demand_range": (20, 150),
        "volatility": 0.25,
        "shelf_life_days": 14
    },
    "bakery": {
        "skus": ["white_bread", "whole_wheat_bread", "sourdough", "bagels",
                 "croissants", "muffins", "donuts", "rolls",
                 "rye_bread", "ciabatta"],
        "base_demand_range": (15, 120),
        "volatility": 0.30,
        "shelf_life_days": 5
    },
    "produce": {
        "skus": ["bananas", "apples", "oranges", "strawberries",
                 "lettuce", "tomatoes", "avocados", "grapes",
                 "cucumbers", "bell_peppers"],
        "base_demand_range": (25, 200),
        "volatility": 0.35,
        "shelf_life_days": 7
    },
    "meat": {
        "skus": ["chicken_breast", "ground_beef", "pork_chops", "salmon",
                 "turkey", "bacon", "sausage", "shrimp",
                 "lamb_chops", "tilapia"],
        "base_demand_range": (10, 80),
        "volatility": 0.20,
        "shelf_life_days": 5
    },
    "deli": {
        "skus": ["ham", "turkey_deli", "salami", "roast_beef",
                 "provolone", "swiss", "coleslaw", "potato_salad",
                 "hummus", "guacamole"],
        "base_demand_range": (8, 60),
        "volatility": 0.22,
        "shelf_life_days": 7
    },
    "frozen": {
        "skus": ["ice_cream_vanilla", "ice_cream_chocolate", "frozen_pizza",
                 "frozen_veggies", "frozen_fruit", "fish_sticks",
                 "frozen_dinners", "popsicles", "frozen_waffles", "frozen_burritos"],
        "base_demand_range": (12, 90),
        "volatility": 0.18,
        "shelf_life_days": 90
    },
    "beverages": {
        "skus": ["orange_juice", "apple_juice", "almond_milk", "oat_milk",
                 "kombucha", "smoothie", "cold_brew", "lemonade",
                 "coconut_water", "protein_shake"],
        "base_demand_range": (15, 100),
        "volatility": 0.20,
        "shelf_life_days": 21
    },
    "prepared_foods": {
        "skus": ["rotisserie_chicken", "mac_and_cheese", "soup_chicken",
                 "soup_tomato", "pasta_salad", "sushi_rolls",
                 "sandwich_club", "wrap_veggie", "quiche", "spring_rolls"],
        "base_demand_range": (5, 50),
        "volatility": 0.35,
        "shelf_life_days": 3
    },
    "snacks": {
        "skus": ["fresh_salsa", "guacamole_snack", "fruit_cups",
                 "veggie_tray", "cheese_platter", "trail_mix_fresh",
                 "granola_bars", "protein_bites", "fresh_cookies", "brownies"],
        "base_demand_range": (10, 70),
        "volatility": 0.28,
        "shelf_life_days": 10
    },
    "floral": {
        "skus": ["roses_red", "roses_mixed", "tulips", "sunflowers",
                 "lilies", "orchids", "carnations", "daisies",
                 "mixed_bouquet", "succulent"],
        "base_demand_range": (3, 30),
        "volatility": 0.40,
        "shelf_life_days": 7
    }
}

US_HOLIDAYS_2023_2025 = [
    # 2023
    "2023-01-01", "2023-01-16", "2023-02-14", "2023-02-20",
    "2023-04-09", "2023-05-29", "2023-07-04", "2023-09-04",
    "2023-10-31", "2023-11-23", "2023-11-24", "2023-12-24",
    "2023-12-25", "2023-12-31",
    # 2024
    "2024-01-01", "2024-01-15", "2024-02-14", "2024-02-19",
    "2024-03-31", "2024-05-27", "2024-07-04", "2024-09-02",
    "2024-10-31", "2024-11-28", "2024-11-29", "2024-12-24",
    "2024-12-25", "2024-12-31",
    # 2025
    "2025-01-01", "2025-01-20", "2025-02-14", "2025-02-17",
    "2025-04-20", "2025-05-26", "2025-07-04", "2025-09-01",
    "2025-10-31", "2025-11-27", "2025-11-28", "2025-12-24",
    "2025-12-25", "2025-12-31",
]

STORE_CONFIGS = {
    "store_{:03d}".format(i): {
        "region": ["northeast", "southeast", "midwest", "southwest", "west"][i % 5],
        "size": ["small", "medium", "large"][i % 3],
        "traffic_multiplier": np.random.uniform(0.6, 1.8)
    }
    for i in range(1, 101)  # 100 stores
}


def generate_holiday_flags(dates: pd.DatetimeIndex) -> pd.Series:
    """Generate binary holiday flags for given dates."""
    holiday_dates = pd.to_datetime(US_HOLIDAYS_2023_2025)
    is_holiday = dates.isin(holiday_dates).astype(int)
    # Also flag day before and after holidays
    pre_holiday = dates.isin(holiday_dates - timedelta(days=1)).astype(int)
    post_holiday = dates.isin(holiday_dates + timedelta(days=1)).astype(int)
    return pd.DataFrame({
        "is_holiday": is_holiday,
        "is_pre_holiday": pre_holiday,
        "is_post_holiday": post_holiday
    })


def generate_seasonality(dates: pd.DatetimeIndex, category: str) -> np.ndarray:
    """Generate category-specific seasonal patterns."""
    day_of_year = dates.dayofyear.values
    
    # Base seasonal pattern (sinusoidal)
    seasonal = np.sin(2 * np.pi * day_of_year / 365.25)
    
    # Category-specific adjustments
    if category in ["produce", "beverages"]:
        # Higher demand in summer
        seasonal = 0.3 * np.sin(2 * np.pi * (day_of_year - 80) / 365.25)
    elif category in ["bakery", "prepared_foods"]:
        # Higher demand in winter/holidays
        seasonal = 0.25 * np.sin(2 * np.pi * (day_of_year - 260) / 365.25)
    elif category == "frozen":
        # Higher demand in summer
        seasonal = 0.2 * np.sin(2 * np.pi * (day_of_year - 80) / 365.25)
    elif category == "floral":
        # Spikes around Valentine's Day, Mother's Day
        valentine_spike = np.exp(-0.5 * ((day_of_year - 45) / 5) ** 2) * 2.0
        mothers_spike = np.exp(-0.5 * ((day_of_year - 130) / 5) ** 2) * 1.5
        seasonal = 0.15 * seasonal + valentine_spike + mothers_spike
    else:
        seasonal = 0.2 * seasonal
    
    return seasonal


def generate_day_of_week_pattern(dates: pd.DatetimeIndex) -> np.ndarray:
    """Generate day-of-week demand patterns (weekends higher)."""
    dow = dates.dayofweek.values
    # Multipliers: Mon=0.9, Tue=0.85, Wed=0.9, Thu=0.95, Fri=1.15, Sat=1.3, Sun=1.1
    multipliers = np.array([0.9, 0.85, 0.9, 0.95, 1.15, 1.3, 1.1])
    return multipliers[dow]


def generate_promotions(n_days: int, promo_frequency: float = 0.08) -> np.ndarray:
    """Generate random promotion events."""
    promos = np.zeros(n_days)
    promo_starts = np.random.random(n_days) < promo_frequency
    for i in range(n_days):
        if promo_starts[i]:
            duration = np.random.randint(1, 5)
            end = min(i + duration, n_days)
            promo_lift = np.random.uniform(1.2, 2.0)
            promos[i:end] = promo_lift
    promos[promos == 0] = 1.0
    return promos


def inject_missing_data(df: pd.DataFrame, missing_rate: float = 0.02) -> pd.DataFrame:
    """Inject realistic missing data patterns."""
    n = len(df)
    # Random missing values
    mask = np.random.random(n) < missing_rate
    df.loc[mask, "sales"] = np.nan
    
    # Occasional multi-day gaps (store closures, system failures)
    n_gaps = max(1, int(n * 0.005))
    for _ in range(n_gaps):
        start = np.random.randint(0, max(1, n - 5))
        gap_len = np.random.randint(1, 4)
        df.iloc[start:start + gap_len, df.columns.get_loc("sales")] = np.nan
    
    return df


def generate_dataset(
    start_date: str = "2023-01-01",
    end_date: str = "2025-03-31",
    n_stores: int = 100,
    missing_rate: float = 0.02,
    output_dir: str = "data",
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate complete synthetic dataset for perishable goods forecasting.
    
    Creates 10,000+ SKU-store combinations with realistic:
    - Seasonal patterns
    - Day-of-week effects
    - Holiday effects
    - Promotional lifts
    - Trend components
    - Random noise
    - Missing data
    
    Args:
        start_date: Start date for data generation
        end_date: End date for data generation
        n_stores: Number of stores (max 100)
        missing_rate: Fraction of data points to set as missing
        output_dir: Directory to save output files
        seed: Random seed for reproducibility
    
    Returns:
        DataFrame with all generated sales data
    """
    np.random.seed(seed)
    
    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    n_days = len(dates)
    store_ids = list(STORE_CONFIGS.keys())[:n_stores]
    
    all_records = []
    total_combinations = 0
    
    logger.info(f"Generating data for {n_stores} stores, {n_days} days...")
    
    for category, config in PERISHABLE_CATEGORIES.items():
        skus = config["skus"]
        base_low, base_high = config["base_demand_range"]
        volatility = config["volatility"]
        shelf_life = config["shelf_life_days"]
        
        # Category-level patterns
        seasonality = generate_seasonality(dates, category)
        dow_pattern = generate_day_of_week_pattern(dates)
        holiday_df = generate_holiday_flags(dates)
        
        for sku in skus:
            sku_base = np.random.uniform(base_low, base_high)
            # SKU-level trend (slight growth or decline)
            sku_trend = np.random.uniform(-0.0003, 0.0005)
            trend = 1 + sku_trend * np.arange(n_days)
            
            for store_id in store_ids:
                store_cfg = STORE_CONFIGS[store_id]
                store_mult = store_cfg["traffic_multiplier"]
                
                # Generate base demand
                base = sku_base * store_mult
                
                # Apply all patterns
                promotions = generate_promotions(n_days)
                noise = np.random.normal(0, volatility * base, n_days)
                
                # Holiday effect (10-50% lift)
                holiday_lift = 1 + holiday_df["is_holiday"].values * np.random.uniform(0.1, 0.5)
                pre_holiday_lift = 1 + holiday_df["is_pre_holiday"].values * np.random.uniform(0.05, 0.2)
                
                # Combine all effects
                sales = (
                    base
                    * trend
                    * (1 + seasonality)
                    * dow_pattern
                    * promotions
                    * holiday_lift
                    * pre_holiday_lift
                    + noise
                )
                
                # Floor at 0 and round
                sales = np.maximum(0, np.round(sales)).astype(int)
                
                records = pd.DataFrame({
                    "date": dates,
                    "store_id": store_id,
                    "sku": f"{category}_{sku}",
                    "category": category,
                    "sales": sales.astype(float),
                    "is_promotion": (promotions > 1.0).astype(int),
                    "promotion_lift": promotions,
                    "is_holiday": holiday_df["is_holiday"].values,
                    "is_pre_holiday": holiday_df["is_pre_holiday"].values,
                    "is_post_holiday": holiday_df["is_post_holiday"].values,
                    "store_region": store_cfg["region"],
                    "store_size": store_cfg["size"],
                    "shelf_life_days": shelf_life,
                    "price": round(np.random.uniform(1.5, 15.0), 2)
                })
                
                all_records.append(records)
                total_combinations += 1
    
    logger.info(f"Generated {total_combinations} SKU-store combinations")
    
    # Combine all records
    df = pd.concat(all_records, ignore_index=True)
    
    # Inject missing data
    df = inject_missing_data(df, missing_rate)
    
    # Sort by date, store, sku
    df = df.sort_values(["date", "store_id", "sku"]).reset_index(drop=True)
    
    # Save to disk
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "sales_data.csv")
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df):,} records to {output_path}")
    
    # Generate summary statistics
    summary = {
        "total_records": len(df),
        "unique_skus": df["sku"].nunique(),
        "unique_stores": df["store_id"].nunique(),
        "sku_store_combinations": total_combinations,
        "date_range": f"{df['date'].min()} to {df['date'].max()}",
        "categories": df["category"].nunique(),
        "missing_rate": df["sales"].isna().mean(),
        "avg_daily_sales": df["sales"].mean(),
    }
    
    logger.info("Dataset Summary:")
    for k, v in summary.items():
        logger.info(f"  {k}: {v}")
    
    return df


if __name__ == "__main__":
    df = generate_dataset(
        start_date="2023-01-01",
        end_date="2025-03-31",
        n_stores=100,
        output_dir="data"
    )
    print(f"\nDataset shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"\nSample:\n{df.head(10)}")
