from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: int
    login: str
    password: str
    devices: list["Device"] = None


@dataclass
class Device:
    id: int
    data: list["Data"] = None


@dataclass
class Data:
    x: float
    y: float
    z: float
    date: datetime


@dataclass
class Analysis:
    begin_date: datetime
    end_date: datetime
    min_value: float
    max_value: float
    count: int
    sum: float
    median: float
