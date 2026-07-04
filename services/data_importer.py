import sqlite3
from pathlib import Path

import pandas as pd

from utils.column_mapper import ColumnMapper
from utils.constants import SEASONS


class DataImporter:
    def __init__(self):
        self.mapper = ColumnMapper()

    def load_file(self, file_path, sqlite_table=None):
        path = Path(file_path)
        suffix = path.suffix.lower()
        if suffix == ".csv":
            return pd.read_csv(path)
        if suffix in {".xls", ".xlsx"}:
            return pd.read_excel(path)
        if suffix in {".db", ".sqlite", ".sqlite3"}:
            with sqlite3.connect(path) as conn:
                table = sqlite_table or self._first_table(conn)
                return pd.read_sql_query(f'SELECT * FROM "{table}"', conn)
        raise ValueError("仅支持 CSV、Excel 和 SQLite 数据文件。")

    def standardize(self, frame, source="upload"):
        mapping = self.mapper.detect(frame.columns)
        data = pd.DataFrame()

        for target, original in mapping.items():
            data[target] = frame[original]

        if "date" in data:
            data["date"] = pd.to_datetime(data["date"], errors="coerce")
            data["year"] = data.get("year", data["date"].dt.year)
            data["month"] = data.get("month", data["date"].dt.month)

        if "month" not in data:
            data["month"] = 1
        data["month"] = pd.to_numeric(data["month"], errors="coerce").fillna(1).astype(int).clip(1, 12)

        if "year" not in data:
            data["year"] = 2025
        data["year"] = pd.to_numeric(data["year"], errors="coerce").fillna(2025).astype(int)

        if "date" not in data:
            data["date"] = pd.to_datetime(
                data["year"].astype(str) + "-" + data["month"].astype(str).str.zfill(2) + "-01"
            )

        if "season" not in data:
            data["season"] = data["month"].map(SEASONS)

        if "disease" not in data:
            data["disease"] = "Unknown"

        if "incidence" not in data:
            data["incidence"] = 1

        for col in ["incidence", "temperature", "humidity", "rainfall", "pm25", "uv_index", "wind_speed"]:
            if col in data:
                data[col] = pd.to_numeric(data[col], errors="coerce")

        data["source"] = source
        return data

    @staticmethod
    def _first_table(conn):
        tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
        if tables.empty:
            raise ValueError("SQLite 文件中没有可读取的数据表。")
        return tables.iloc[0]["name"]

