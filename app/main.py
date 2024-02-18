import uvicorn
import asyncio
from datetime import datetime
from typing import Annotated
from fastapi import FastAPI, Response, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from database.base import init_models
from database.accessor import BaseAccessor
from web.schemas import DataSchema, AnalysisSchema, UserSchema, DeviceSchema

app = FastAPI()
db = BaseAccessor()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@app.get("/")
async def root():
    hi_message = (
        "Hi, this is a system for recording and analyzing data coming from some device!"
    )
    return Response(content=hi_message)


@app.post("/add_user/")
async def add_user(user_info: UserSchema):
    user = await db.add_user(user_info.login, user_info.password)
    if not user:
        return Response(
            content=f"User with login '{user_info.login}' already exists!",
            status_code=status.HTTP_409_CONFLICT,
        )
    return {"id": user.id, "login": user.login, "password": user.password}


@app.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    token = await db.auth_user(form_data.username, form_data.password)
    if not token:
        return Response(
            content="Invalid login or password!",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    return {"access_token": token, "token_type": "bearer"}


@app.get("/users/me", response_model=UserSchema)
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = await db.get_user_by_token(token)
    if not user:
        return Response(
            content="User not found!",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return {"login": user.login, "password": user.password}


@app.post("/add_device/")
async def add_device(
    device_info: DeviceSchema, token: Annotated[str, Depends(oauth2_scheme)]
):
    user = await db.get_user_by_token(token)
    if not user:
        return Response(
            content=f"User not found!",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    device = await db.add_device(device_info.id, user.id)
    if not device:
        return Response(
            content=f"Device with id = {device_info.id} already exists!",
            status_code=status.HTTP_409_CONFLICT,
        )
    return {"id": device.id}


@app.get("/devices/")
async def get_all_devices():
    devices = await db.get_devices()
    if devices is None:
        return Response(
            content=f"No devices found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    list_id = [device.id for device in devices]
    response = {"device_ids": list_id}
    return response


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


@app.get("/device_data_analysis/")
async def device_data_analysis(
    device_id: int = None,
    user_id: int = None,
    column: str = None,
    begin: datetime = datetime(1753, 1, 1, 0, 0, 0),
    end: datetime = datetime(9999, 12, 31, 23, 59, 59),
):
    analysis = await db.get_analysis(device_id, user_id, column, begin, end)
    if not analysis:
        return Response(content="No data yet.")
    response = dict()
    for column_analysis in analysis:
        response[column_analysis.column] = {
            "begin_date": column_analysis.begin_date,
            "end_date": column_analysis.end_date,
            "min_value": column_analysis.min_value,
            "max_value": column_analysis.max_value,
            "count": column_analysis.count,
            "sum": column_analysis.sum,
            "median": column_analysis.median,
        }
    if device_id:
        response = {device_id: response}
    elif user_id:
        response = {user_id: response}
    return response


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_models())
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
