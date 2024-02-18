from locust import HttpUser, task
import random


class User(HttpUser):
    def on_start(self):
        self.rand = random.random() * 10**6
        random_str = str(self.rand)
        login = "login" + random_str
        password = "password" + random_str

        user_info = {"login": login, "password": password}
        resp = self.client.post("/add_user", json=user_info)
        self.user_id = resp.json()["id"]

        data = {"username": login, "password": password}
        resp = self.client.post(
            "/login",
            data=data,
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        token = resp.json()["access_token"]
        self.auth_header = {
            "content-type": "application/json",
            "Authorization": "Bearer " + token,
        }
        device_id = round(self.rand)
        device_info = {"id": device_id}
        self.client.post("/add_device", json=device_info, headers=self.auth_header)


class Root(User):
    @task
    def root(self):
        self.client.get("/")


class GetCurrentUser(User):
    @task
    def get_current_user(self):
        self.client.get("/users/me", headers=self.auth_header)


class NewDeviceData(User):
    @task
    def new_device_data(self):
        resp = self.client.get("/devices")
        list_id = resp.json()["device_ids"]
        device_id = list_id[random.randint(0, len(list_id) - 1)]
        self.client.get(f"/new_device_data/{device_id}")


class OneDeviceDA(User):
    @task
    def one_device_data_analysis(self):
        resp = self.client.get("/devices")
        list_id = resp.json()["device_ids"]
        device_id = list_id[random.randint(0, len(list_id) - 1)]
        self.client.get(f"/device_data_analysis/?device_id={device_id}")


class UserDevicesDA(User):
    @task
    def user_devices_data_analysis(self):
        self.client.get(f"/device_data_analysis/?user_id={self.user_id}")


class AllDevicesDA(User):
    @task
    def all_devices_data_analysis(self):
        self.client.get(f"/device_data_analysis")
