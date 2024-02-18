import os

DATABASE_URL = os.environ.get("DATABASE_URL")

JWT_SECRET = "some_secret_key"
JWT_ALGORITHM = "HS256"
