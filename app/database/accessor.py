import time
from datetime import datetime
from hashlib import sha256

import jwt
from config import JWT_ALGORITHM, JWT_SECRET
from database.base import async_session
from database.dataclasses import Analysis, Data, Device, User
from database.models import DataModel, DeviceModel, UserModel
from devices.device_simulator import SomeDevice
from sqlalchemy import func, insert, select
from sqlalchemy.dialects.postgresql import insert as insert_psql


class BaseAccessor:
    def __init__(self) -> None:
        self.session = async_session

    async def add_user(self, login: str, password_str: str) -> User:
        password = sha256(password_str.encode("utf-8")).hexdigest()
        stmt = (
            insert_psql(UserModel)
            .values(login=login, password=password)
            .returning(UserModel)
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=["login"])
        async with self.session() as session:
            user_obj = await session.scalar(stmt)
            await session.commit()
            if not user_obj:
                return None
            user = User(
                id=user_obj.id, login=user_obj.login, password=user_obj.password
            )
        return user

    async def get_user(self, id: int = None, login: str = None) -> User:
        stmt = select(UserModel)
        if id:
            stmt = stmt.where(UserModel.id == id)
        elif login:
            stmt = stmt.where(UserModel.login == login)
        else:
            return None
        async with self.session() as session:
            user_obj = await session.scalar(stmt)
            if not user_obj:
                return None
            user = User(
                id=user_obj.id, login=user_obj.login, password=user_obj.password
            )
        devices = await self.get_devices(id)
        user.devices = devices
        return user

    async def auth_user(self, login: str, password_str: str) -> str:
        user = await self.get_user(login=login)
        if not user:
            return None
        password = sha256(password_str.encode("utf-8")).hexdigest()
        if password != user.password:
            return None
        payload = {"user_id": user.id, "expires": time.time() + 86400}
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token

    async def get_user_by_token(self, token: str) -> User:
        try:
            decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except:
            return None
        if decoded_token["expires"] < time.time():
            return None
        user = await self.get_user(id=decoded_token["user_id"])
        return user

    async def add_device(self, id: int, user_id: int) -> Device:
        stmt = (
            insert_psql(DeviceModel)
            .values(id=id, user_id=user_id)
            .returning(DeviceModel)
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=["id"])
        async with self.session() as session:
            device_obj = await session.scalar(stmt)
            await session.commit()
            if not device_obj:
                return None
            device = Device(id=device_obj.id)
        return device

    async def get_devices(self, user_id: int = None) -> list[Device]:
        stmt = select(DeviceModel)
        if user_id:
            stmt = stmt.join(UserModel, UserModel.id == DeviceModel.user_id).where(
                UserModel.id == user_id
            )
        async with self.session() as session:
            device_objs = await session.scalars(stmt)
            devices = []
            if not device_objs:
                return None
            for device_obj in device_objs:
                devices.append(Device(id=device_obj.id))
        return devices

    async def get_device(self, id: int) -> Device:
        stmt = select(DeviceModel).where(DeviceModel.id == id)
        async with self.session() as session:
            device_obj = await session.scalar(stmt)
            if not device_obj:
                return None
            device = Device(id=device_obj.id)
        return device

    async def new_data(self, device_id: int) -> Data:
        x, y, z = SomeDevice.get_data()
        stmt = (
            insert(DataModel)
            .values(x=x, y=y, z=z, device_id=device_id)
            .returning(DataModel)
        )

        async with self.session() as session:
            data_obj = await session.scalar(stmt)
            await session.commit()
            data = Data(
                x=x,
                y=y,
                z=z,
                date=data_obj.date,
            )
        return data

    async def get_all_data(self) -> list[Data]:
        stmt = select(DataModel)
        async with self.session() as session:
            data_objs = await session.scalars(stmt)
            if not data_objs:
                return None
            data = []
            for data_obj in data_objs:
                data.append(
                    Data(
                        x=data_obj.x,
                        y=data_obj.y,
                        z=data_obj.z,
                        date=data_obj.date,
                    )
                )
        return data

    async def get_device_data(self, id: int) -> list[Data]:
        stmt = (
            select(DataModel)
            .join(DeviceModel, DeviceModel.id == DataModel.device_id)
            .where(DeviceModel.id == id)
            .order_by(DataModel.date)
        )
        async with self.session() as session:
            data_objs = await session.scalars(stmt)
            if not data_objs:
                return None
            data = []
            for data_obj in data_objs:
                data.append(
                    Data(
                        x=data_obj.x,
                        y=data_obj.y,
                        z=data_obj.z,
                        date=data_obj.date,
                    )
                )
        return data

    async def get_user_data(self, id: int) -> list[Data]:
        stmt = (
            select(DataModel)
            .join(DeviceModel, DeviceModel.id == DataModel.device_id)
            .join(UserModel, UserModel.id == DeviceModel.id)
            .where(UserModel.id == id)
            .order_by(DataModel.date)
        )
        async with self.session() as session:
            data_objs = await session.scalars(stmt)
            if not data_objs:
                return None
            data = []
            for data_obj in data_objs:
                data.append(
                    Data(
                        x=data_obj.x,
                        y=data_obj.y,
                        z=data_obj.z,
                        date=data_obj.date,
                    )
                )
        return data

    async def get_total_period(self) -> list[datetime]:
        data = await self.get_all_data()
        if not data:
            return None
        return [data[0].date, data[-1].date]

    async def get_device_period(self, id: int) -> list[datetime]:
        device_data = await self.get_device_data(id)
        if not device_data:
            return None
        return [device_data[0].date, device_data[-1].date]

    async def get_user_period(self, id: int) -> list[datetime]:
        user_data = await self.get_user_data(id)
        if not user_data:
            return None
        return [user_data[0].date, user_data[-1].date]

    async def get_analysis(
        self,
        device_id: int = None,
        user_id: int = None,
        column: str = None,
        begin: datetime = datetime(1753, 1, 1, 0, 0, 0),
        end: datetime = datetime(9999, 12, 31, 23, 59, 59),
    ) -> list[Analysis]:
        if device_id:
            period = await self.get_device_period(device_id)
        elif user_id:
            period = await self.get_user_period(user_id)
        else:
            period = await self.get_total_period()

        if not period:
            return None

        if begin < period[0]:
            begin_date = period[0]
        else:
            begin_date = begin

        if end > period[1]:
            end_date = period[1]
        else:
            end_date = end

        if column in {"x", "y", "z"}:
            analysis = await self.column_analysis(
                column, begin_date, end_date, device_id, user_id
            )
            return [analysis]

        analysis = []
        for column in {"x", "y", "z"}:
            column_analysis = await self.column_analysis(
                column, begin_date, end_date, device_id, user_id
            )
            analysis.append(column_analysis)
        return analysis

    async def column_analysis(
        self,
        column: str,
        begin_date: datetime,
        end_date: datetime,
        device_id: int = None,
        user_id: int = None,
    ) -> Analysis:
        analyst = Data_Analyst(column, begin_date, end_date, device_id, user_id)
        min_value = await analyst.min_value()
        max_value = await analyst.max_value()
        count = await analyst.count()
        sum = await analyst.sum()
        median = await analyst.median()

        return Analysis(
            column=column,
            begin_date=begin_date,
            end_date=end_date,
            min_value=min_value,
            max_value=max_value,
            count=count,
            sum=sum,
            median=median,
        )


class Data_Analyst:
    def __init__(
        self,
        column_name: str,
        begin: datetime,
        end: datetime,
        device_id: int = None,
        user_id: int = None,
    ) -> None:
        self.session = async_session
        if device_id:
            self.device_id = device_id
            self.operation = self.operation_for_one_device
        elif user_id:
            self.user_id = user_id
            self.operation = self.operation_for_user_devices
        else:
            self.operation = self.operation_for_all
        self.begin_date = begin
        self.end_date = end
        match column_name:
            case "x":
                self.column = DataModel.x
            case "y":
                self.column = DataModel.y
            case "z":
                self.column = DataModel.z

    async def operation_for_one_device(self, select_arg: callable) -> float:
        stmt = (
            select(select_arg(self.column))
            .join(DeviceModel, DeviceModel.id == DataModel.device_id)
            .where(
                (DeviceModel.id == self.device_id)
                & (DataModel.date >= self.begin_date)
                & (DataModel.date <= self.end_date)
            )
        )
        async with self.session() as session:
            result = await session.scalar(stmt)
        return result

    async def operation_for_user_devices(self, select_arg: callable) -> float:
        stmt = (
            select(select_arg(self.column))
            .join(DeviceModel, DeviceModel.id == DataModel.device_id)
            .join(UserModel, UserModel.id == DeviceModel.user_id)
            .where(
                (UserModel.id == self.user_id)
                & (DataModel.date >= self.begin_date)
                & (DataModel.date <= self.end_date)
            )
        )
        async with self.session() as session:
            result = await session.scalar(stmt)
        return result

    async def operation_for_all(self, select_arg: callable) -> float:
        stmt = (
            select(select_arg(self.column))
            .join(DeviceModel, DeviceModel.id == DataModel.device_id)
            .where(
                (DataModel.date >= self.begin_date) & (DataModel.date <= self.end_date)
            )
        )
        async with self.session() as session:
            result = await session.scalar(stmt)
        return result

    async def min_value(self) -> float:
        min = await self.operation(func.min)
        return min

    async def max_value(self) -> float:
        max = await self.operation(func.max)
        return max

    async def count(self) -> int:
        count = await self.operation(func.count)
        return count

    async def sum(self) -> float:
        sum = await self.operation(func.sum)
        return sum

    async def median(self) -> float:
        median = await self.operation(func.percentile_cont(0.5).within_group)
        return median
