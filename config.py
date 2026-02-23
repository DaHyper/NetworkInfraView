import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(DATA_DIR, exist_ok=True)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(DATA_DIR, 'networkinfraview.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    APP_NAME = "NetworkInfraView"
    VERSION = "1.0"
