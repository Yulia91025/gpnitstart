import os
import asyncio
from datetime import datetime
from fastapi import FastAPI, Response, status

from database.base import init_models
from database.accessor import BaseAccessor
from web.schemas import DataSchema, AnalysisSchema

app = FastAPI()
db = BaseAccessor()


@app.get("/")
async def root():
    return Response(content="Hello world!")


@app.get("/new_device_data/{id}", response_model=DataSchema)
async def new_device_data(id: int):
    device = await db.get_device(id)
    if device is None:
        return Response(
            content=f"Device with id = {id} not found!",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    data = await db.new_data(id)
    response = {"x": data.x, "y": data.y, "z": data.z, "date": data.date}
    return response


@app.get("/device_data_analysis/{id}", response_model=AnalysisSchema)
async def device_data_analysis(
    id: int,
    column: str = None,
    begin: datetime = datetime(1753, 1, 1, 0, 0, 0),
    end: datetime = datetime(9999, 12, 31, 23, 59, 59),
):
    analysis = await db.get_analysis(id, column, begin, end)
    return {
        "begin_date": analysis.begin_date,
        "end_date": analysis.end_date,
        "min_value": analysis.min_value,
        "max_value": analysis.max_value,
        "count": analysis.count,
        "sum": analysis.sum,
        "median": analysis.median,
    }


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_models())
    os.system("uvicorn main:app --host 0.0.0.0 --port 80")
