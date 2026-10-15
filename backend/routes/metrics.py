"""Metrics endpoints."""
from fastapi import APIRouter, Request
from typing import Dict

router = APIRouter()


@router.get("/metrics")
async def get_metrics(req: Request) -> Dict:
    """Get model performance metrics."""
    model_mgr = req.app.state.model_manager
    return {"metrics": model_mgr.get_metrics()}


@router.get("/metrics/skus")
async def get_available_skus() -> Dict:
    """Get list of available SKUs for selection."""
    import os, json
    categories = {
        "dairy": ["whole_milk", "skim_milk", "yogurt_plain", "yogurt_fruit",
                   "cheddar_cheese", "mozzarella", "cream_cheese", "butter",
                   "cottage_cheese", "sour_cream"],
        "bakery": ["white_bread", "whole_wheat_bread", "sourdough", "bagels",
                   "croissants", "muffins", "donuts", "rolls", "rye_bread", "ciabatta"],
        "produce": ["bananas", "apples", "oranges", "strawberries",
                    "lettuce", "tomatoes", "avocados", "grapes", "cucumbers", "bell_peppers"],
        "meat": ["chicken_breast", "ground_beef", "pork_chops", "salmon",
                 "turkey", "bacon", "sausage", "shrimp", "lamb_chops", "tilapia"],
        "deli": ["ham", "turkey_deli", "salami", "roast_beef", "provolone",
                "swiss", "coleslaw", "potato_salad", "hummus", "guacamole"],
    }
    skus = []
    for cat, items in categories.items():
        for item in items:
            skus.append({"sku": f"{cat}_{item}", "category": cat, "name": item.replace("_", " ").title()})
    
    stores = [f"store_{i:03d}" for i in range(1, 101)]
    return {"skus": skus, "stores": stores, "categories": list(categories.keys())}
