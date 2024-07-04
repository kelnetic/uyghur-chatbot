from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
from enum import Enum
from datetime import date

class Message(BaseModel):
    content: str
    chat_password: str

class CategoryTypes(str, Enum):
    REPORT = "Report",
    BRIEF = "Brief",
    TESTIMONY = "Testimony",
    RESEARCH = "Research",
    NEWS = "News",
    ANALYSIS = "Analysis"

class Dataset(BaseModel):
    file_name: str
    source_link: str
    title: str
    primary_category: CategoryTypes
    document_origin: str
    publication_year: int
    publication_month: int
    publication_day: Optional[int] = None

    @model_validator(mode="after")
    def validate_publication_date(cls, values):
        pub_year = values.publication_year
        pub_month = values.publication_month
        pub_day = values.publication_day
        if pub_day:
            try:
                date(pub_year, pub_month, pub_day)
            except ValueError as value_error:
                raise ValueError(f"publication date: {value_error}")
        else:
            if pub_year < 1 or pub_year > 9999:
                raise ValueError("publication year: year out of range")
            if pub_month < 1 or pub_month > 12:
                raise ValueError("publication month: month out of range")
        return values

    @field_validator("file_name")
    def validate_file_name(cls, file_name):
        if file_name.count(".") > 1:
            raise ValueError("File names cannot have periods")
        return file_name