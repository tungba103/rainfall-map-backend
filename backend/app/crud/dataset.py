from sqlmodel import select
from typing import List, Optional
from app.models.dataset import Dataset
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, cast, String, text

async def get_datasets(db: AsyncSession, skip: int = 0, limit: int = 10, product_name: Optional[str] = None) -> List[Dataset]:
    query = select(Dataset).offset(skip).limit(limit)
    
    if product_name:
        # Adjusting JSON path query with cast to string
        query = query.where(text("CAST(metadata->'product'->>'name' AS VARCHAR) = :product_name")).params(product_name=product_name)

        # Debugging: print the generated SQL query
        print("Generated Query:", query, product_name)

    result = await db.execute(query)
    datasets = result.scalars().all()
    
    # Debugging: print filtered results to verify correctness
    print("Filtered Datasets:", datasets)
    
    return datasets


async def create_dataset(db: AsyncSession, dataset: Dataset) -> Dataset:
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    return dataset

async def get_dataset(db: AsyncSession, dataset_id: str) -> Dataset:
    return await db.get(Dataset, dataset_id)

async def update_dataset(db: AsyncSession, dataset_id: str, updates: Dataset) -> Dataset:
    dataset = await get_dataset(db, dataset_id)
    if dataset:
        for key, value in updates.dict(exclude_unset=True).items():
            setattr(dataset, key, value)
        await db.commit()
        await db.refresh(dataset)
    return dataset

async def delete_dataset(db: AsyncSession, dataset_id: str) -> Dataset:
    dataset = await get_dataset(db, dataset_id)
    if dataset:
        await db.delete(dataset)
        await db.commit()
    return dataset
