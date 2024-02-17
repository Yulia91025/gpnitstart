from sqlalchemy import select, insert, update, func
from database.base import async_session
from database.models import UserModel, DeviceModel, DataModel
from database.dataclasses import User, Device, Data, Analysis
from devices.device_simulator import SomeDevice
from datetime import datetime


class BaseAccessor:
    def __init__(self) -> None:
        self.session = async_session

    async def add_device(self, id: int = None) -> int:
        stmt = insert(DeviceModel).values(id=id)

        async with self.session() as session:
            result = await session.execute(stmt)
            await session.commit()

    async def get_all_devices(self) -> list[Device]:
        stmt = select(DeviceModel)
        async with self.session() as session:
            result = await session.execute(stmt)
            devices = []
            device_objs = result.scalars()
            if not device_objs:
                return None
            for device_obj in device_objs:
                devices.append(Device(id=device_obj.id))
        return devices

    async def get_device(self, id: int) -> Device:
        stmt = select(DeviceModel).where(DeviceModel.id == id)
        async with self.session() as session:
            result = await session.execute(stmt)
            device_obj = result.scalar()
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

    async def get_device_data(self, id: int) -> list[Data]:
        stmt = (
            select(DataModel)
            .join(DeviceModel, DeviceModel.id == DataModel.device_id)
            .where(DeviceModel.id == id)
            .order_by(DataModel.date)
        )
        async with self.session() as session:
            result = await session.execute(stmt)
            data_objs = result.scalars()
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

    async def get_period(self, id: int) -> list[datetime]:
        device_data = await self.get_device_data(id)
        return [device_data[0].date, device_data[-1].date]

    async def get_analysis(
        self,
        id: int,
        column: str = None,
        begin: datetime = datetime(1753, 1, 1, 0, 0, 0),
        end: datetime = datetime(9999, 12, 31, 23, 59, 59),
    ) -> Analysis:
        period = await self.get_period(id)
        if begin < period[0]:
            begin_date = period[0]
        else:
            begin_date = begin

        if end > period[1]:
            end_date = period[1]
        else:
            end_date = end

        if column in {"x", "y", "z"}:
            analyst = Data_Analyst(id, column, begin_date, end_date)
        else:
            analyst = Data_Analyst(id, "x", begin_date, end_date)

        min_value = await analyst.min_value()
        max_value = await analyst.max_value()
        count = await analyst.count()
        sum = await analyst.sum()
        median = await analyst.median()

        return Analysis(
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
        self, device_id: int, column_name: str, begin: datetime, end: datetime
    ) -> None:
        self.session = async_session
        self.device_id = device_id
        self.begin_date = begin
        self.end_date = end
        match column_name:
            case "x":
                self.column = DataModel.x
            case "y":
                self.column = DataModel.y
            case "z":
                self.column = DataModel.z

    async def operation(self, select_arg: callable) -> float:
        stmt = (
            select(select_arg(self.column))
            .join(DeviceModel, DeviceModel.id == DataModel.device_id)
            .where(
                (DeviceModel.id == self.device_id)
                & (DataModel.date >= self.begin_date)
                & ((DataModel.date <= self.end_date))
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
