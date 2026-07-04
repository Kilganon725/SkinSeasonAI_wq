import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "skin-season-ai-dev-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'database' / 'skinseasonai.sqlite3'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = BASE_DIR / "data" / "raw"
    PROCESSED_FOLDER = BASE_DIR / "data" / "processed"
    REPORT_FOLDER = BASE_DIR / "reports"
    DATASET_IMAGE_ROOT = BASE_DIR / "datasets" / "SkinDisease"
    IMAGE_MODEL_PATH = BASE_DIR / "models" / "skin_disease_image_classifier.joblib"
    IMAGE_UPLOAD_FOLDER = BASE_DIR / "static" / "uploads" / "diagnosis"
    MAX_CONTENT_LENGTH = 64 * 1024 * 1024
