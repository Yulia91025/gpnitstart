from pydantic import BaseModel
from datetime import datetime


class DataSchema(BaseModel):
    x: float
    y: float
    z: float
    date: datetime


class AnalysisSchema(BaseModel):
    begin_date: datetime
    end_date: datetime
    min_value: float
    max_value: float
    count: int
    sum: float
    median: float
