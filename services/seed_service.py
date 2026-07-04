from datetime import date
from pathlib import Path

import pandas as pd

from app import db
from app.models import DiseaseRecord, User
from config import Config
from services.data_cleaner import DataCleaner
from utils.constants import DATASET_DISEASE_MAP, DISEASE_CATEGORIES, SEASONS


class SeedService:
    def ensure_default_data(self):
        self._ensure_user()
        if DiseaseRecord.query.first() is None:
            frame = self._build_from_image_dataset()
            self.save_records(frame)

    def _ensure_user(self):
        if User.query.filter_by(username="admin").first() is None:
            user = User(username="admin")
            user.set_password("admin123")
            db.session.add(user)
            db.session.commit()

    def _build_from_image_dataset(self):
        root = Path(Config.DATASET_IMAGE_ROOT)
        rows = []
        year = 2025
        for split in ["train", "test"]:
            split_dir = root / split
            if not split_dir.exists():
                continue
            for disease_dir in split_dir.iterdir():
                if not disease_dir.is_dir():
                    continue
                disease = DATASET_DISEASE_MAP.get(disease_dir.name)
                if not disease:
                    continue
                count = len([p for p in disease_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"}])
                if count == 0:
                    continue
                monthly_weights = self._seasonal_weights(disease)
                for month, weight in enumerate(monthly_weights, start=1):
                    incidence = max(1, round(count * weight / sum(monthly_weights)))
                    rows.append(
                        {
                            "date": date(year, month, 1),
                            "year": year,
                            "month": month,
                            "season": SEASONS[month],
                            "disease": disease,
                            "incidence": incidence,
                            "temperature": self._temperature(month),
                            "humidity": self._humidity(month),
                            "rainfall": self._rainfall(month),
                            "pm25": self._pm25(month),
                            "uv_index": self._uv(month),
                            "wind_speed": self._wind(month),
                            "source": f"image_dataset_{split}",
                        }
                    )
        if not rows:
            rows = self._fallback_rows()
        frame = pd.DataFrame(rows)
        frame = frame.groupby(
            ["date", "year", "month", "season", "disease", "source"], as_index=False
        ).agg(
            {
                "incidence": "sum",
                "temperature": "mean",
                "humidity": "mean",
                "rainfall": "mean",
                "pm25": "mean",
                "uv_index": "mean",
                "wind_speed": "mean",
            }
        )
        cleaned, _ = DataCleaner().clean(frame)
        processed = Path(Config.PROCESSED_FOLDER)
        processed.mkdir(parents=True, exist_ok=True)
        cleaned.to_csv(processed / "skinseasonai_seed_from_images.csv", index=False)
        return cleaned

    def save_records(self, frame):
        for row in frame.to_dict(orient="records"):
            record = DiseaseRecord(
                date=pd.to_datetime(row.get("date")).date() if row.get("date") is not None else None,
                year=int(row.get("year", 2025)),
                month=int(row.get("month", 1)),
                season=row.get("season"),
                disease=row.get("disease"),
                incidence=float(row.get("incidence", 0)),
                temperature=float(row.get("temperature", 0)),
                humidity=float(row.get("humidity", 0)),
                rainfall=float(row.get("rainfall", 0)),
                pm25=float(row.get("pm25", 0)),
                uv_index=float(row.get("uv_index", 0)),
                wind_speed=float(row.get("wind_speed", 0)),
                source=row.get("source"),
            )
            db.session.add(record)
        db.session.commit()

    @staticmethod
    def _seasonal_weights(disease):
        return {
            "Eczema": [1.5, 1.4, 1.2, 1.0, 0.9, 0.8, 0.8, 0.9, 1.0, 1.2, 1.3, 1.5],
            "Dermatitis": [1.2, 1.1, 1.2, 1.3, 1.1, 1.0, 0.9, 0.9, 1.1, 1.3, 1.2, 1.2],
            "Psoriasis": [1.3, 1.2, 1.0, 0.9, 0.8, 0.8, 0.7, 0.7, 0.9, 1.0, 1.2, 1.4],
            "Acne": [0.9, 0.9, 1.0, 1.1, 1.2, 1.4, 1.5, 1.5, 1.2, 1.0, 0.9, 0.9],
            "Fungal Infection": [0.7, 0.8, 0.9, 1.0, 1.2, 1.5, 1.7, 1.6, 1.2, 0.9, 0.8, 0.7],
            "Allergic Skin Disease": [0.8, 0.9, 1.4, 1.6, 1.5, 1.2, 1.0, 0.9, 1.0, 1.1, 0.9, 0.8],
        }.get(disease, [1] * 12)

    @staticmethod
    def _temperature(month):
        return [2, 5, 10, 16, 22, 27, 31, 30, 25, 18, 11, 5][month - 1]

    @staticmethod
    def _humidity(month):
        return [54, 56, 60, 64, 68, 74, 78, 77, 70, 63, 58, 55][month - 1]

    @staticmethod
    def _rainfall(month):
        return [18, 25, 42, 58, 72, 105, 140, 126, 82, 48, 30, 20][month - 1]

    @staticmethod
    def _pm25(month):
        return [72, 65, 55, 45, 38, 32, 28, 30, 36, 45, 58, 70][month - 1]

    @staticmethod
    def _uv(month):
        return [2, 3, 4, 6, 7, 9, 10, 9, 7, 5, 3, 2][month - 1]

    @staticmethod
    def _wind(month):
        return [2.2, 2.4, 2.8, 3.0, 2.6, 2.1, 1.8, 1.7, 2.0, 2.3, 2.5, 2.4][month - 1]

    def _fallback_rows(self):
        rows = []
        for disease in DISEASE_CATEGORIES:
            for month in range(1, 13):
                rows.append(
                    {
                        "date": date(2025, month, 1),
                        "year": 2025,
                        "month": month,
                        "season": SEASONS[month],
                        "disease": disease,
                        "incidence": 20 + month,
                        "temperature": self._temperature(month),
                        "humidity": self._humidity(month),
                        "rainfall": self._rainfall(month),
                        "pm25": self._pm25(month),
                        "uv_index": self._uv(month),
                        "wind_speed": self._wind(month),
                        "source": "fallback",
                    }
                )
        return rows

