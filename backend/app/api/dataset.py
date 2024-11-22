from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.db import get_session
from app.models.dataset import Dataset
from app.crud.dataset import create_dataset, get_dataset, get_datasets, update_dataset, delete_dataset

router = APIRouter()

@router.post("/", response_model=Dataset)
async def api_create_dataset(dataset: Dataset, db: AsyncSession = Depends(get_session)):
    return await create_dataset(db, dataset)

@router.get("/", response_model=List[Dataset])
async def api_get_datasets(
    skip: int = 0,
    limit: int = 10,
    product_name: Optional[str] = Query(None, description="Filter by product name in metadata"),
    db: AsyncSession = Depends(get_session)
):
    return await get_datasets(db, skip=skip, limit=limit, product_name=product_name)

@router.put("/{dataset_id}", response_model=Dataset)
async def api_update_dataset(dataset_id: str, updates: Dataset, db: AsyncSession = Depends(get_session)):
    updated_dataset = await update_dataset(db, dataset_id, updates)
    if not updated_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return updated_dataset

@router.delete("/{dataset_id}", response_model=Dataset)
async def api_delete_dataset(dataset_id: str, db: AsyncSession = Depends(get_session)):
    dataset = await delete_dataset(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset
