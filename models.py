from pydantic import BaseModel, field_validator
from typing import Optional
from enum import Enum
from datetime import date

class Message(BaseModel):
    content: str

class CategoryTypes(str, Enum):
    REPORT = "Report",
    TESTIMONY = "Testimony"

class Dataset(BaseModel):
    file_name: str
    source_link: str
    title: str
    primary_category: CategoryTypes
    document_origin: str
    publication_date: Optional[date]

    @field_validator("file_name")
    def validate_file_name(cls, file_name: str) -> str:
        if file_name.count(".") > 1:
            raise ValueError("File names cannot have periods")
        return file_name