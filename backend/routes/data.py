"""Data upload and management endpoints."""
import os
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.schemas import DataUploadResponse
from backend.config import settings

router = APIRouter()


@router.post("/upload_data", response_model=DataUploadResponse)
async def upload_data(file: UploadFile = File(...)):
    """Upload CSV/Excel sales data."""
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(400, "Only CSV and Excel files are supported")
    
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    save_path = os.path.join(settings.DATA_DIR, file.filename)
    
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)
    
    # Parse to count records
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(save_path)
        else:
            df = pd.read_excel(save_path)
        n_records = len(df)
    except Exception as e:
        raise HTTPException(400, f"Error parsing file: {str(e)}")
    
    return DataUploadResponse(
        message="Data uploaded successfully",
        records_processed=n_records,
        filename=file.filename
    )


@router.get("/datasets")
async def list_datasets():
    """List available datasets."""
    data_dir = settings.DATA_DIR
    if not os.path.exists(data_dir):
        return {"datasets": []}
    
    datasets = []
    for f in os.listdir(data_dir):
        if f.endswith(('.csv', '.xlsx')):
            path = os.path.join(data_dir, f)
            size_mb = os.path.getsize(path) / (1024 * 1024)
            datasets.append({"filename": f, "size_mb": round(size_mb, 2)})
    
    return {"datasets": datasets}


@router.get("/data/sample")
async def get_data_sample(filename: str = "sales_data.csv", n: int = 100):
    """Get a sample of data for preview."""
    path = os.path.join(settings.DATA_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(404, "Dataset not found")
    
    df = pd.read_csv(path, nrows=n)
    return {"columns": list(df.columns), "data": df.to_dict("records"), "total_rows": n}
