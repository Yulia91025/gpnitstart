from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.base import Base


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, autoincrement=True, primary_key=True)
    login = Column(String, unique=True)
    password = Column(String)


class DeviceModel(Base):
    __tablename__ = "devices"

    id = Column(Integer, autoincrement=False, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("UserModel")


class DataModel(Base):
    __tablename__ = "data"

    id = Column(Integer, autoincrement=True, primary_key=True)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)
    date = Column(DateTime(), server_default=func.now())
    device_id = Column(Integer, ForeignKey("devices.id"))

    device = relationship("DeviceModel")
