from sqlmodel import Field, SQLModel
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import Column, JSON  # Import JSON and Column from SQLAlchemy

class Dataset(SQLModel, table=True):
    __tablename__ = "dataset"
    __table_args__ = {"schema": "agdc"}

    id: str = Field(primary_key=True, index=True)
    metadata_type_ref: int = Field(index=True, alias="metadata_type_id")  # Assuming ref columns are foreign keys
    dataset_type_ref: int = Field(index=True, alias="dataset_type_id")
    meta_data: Dict = Field(default_factory=dict, sa_column=Column("metadata", JSON))  # Renamed to meta_data
    archived: Optional[datetime] = None  # Adjusted to timestamp
    added: datetime = Field(default_factory=datetime.utcnow)
    added_by: str = Field(default="CURRENT_USER", max_length=63)  # Assuming 63 characters for name
    updated: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True
