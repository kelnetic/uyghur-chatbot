from pydantic import BaseModel
from enum import Enum

class Message(BaseModel):
    content: str

class CategoryTypes(str, Enum):
    REPORT = "Report"

class Dataset(BaseModel):
    file_path: str
    source_link: str
    title: str
    primary_category: CategoryTypes
    document_origin: str
