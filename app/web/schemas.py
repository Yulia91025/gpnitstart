from pydantic import BaseModel
from datetime import datetime


class UserSchema(BaseModel):
    login: str
    password: str


class DeviceSchema(BaseModel):
    id: int


class DataSchema(BaseModel):
    x: float
    y: float
    z: float
    date: datetime


class AnalysisSchema(BaseModel):
    column: str
    begin_date: datetime
    end_date: datetime
    min_value: float
    max_value: float
    count: int
    sum: float
    median: float
