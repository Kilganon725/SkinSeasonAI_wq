import pandas as pd
from sklearn.preprocessing import MinMaxScaler


class DataCleaner:
    NUMERIC_COLUMNS = ["incidence", "temperature", "humidity", "rainfall", "pm25", "uv_index", "wind_speed"]

    def clean(self, frame, normalize=False):
        data = frame.copy()
        before_rows = len(data)
        data = data.drop_duplicates()

        for col in self.NUMERIC_COLUMNS:
            if col in data:
                data[col] = pd.to_numeric(data[col], errors="coerce")
                median = data[col].median()
                data[col] = data[col].fillna(0 if pd.isna(median) else median)
                data[col] = self._cap_outliers(data[col])

        for col in ["disease", "season", "source"]:
            if col in data:
                data[col] = data[col].fillna("Unknown").astype(str)

        if "date" in data:
            data["date"] = pd.to_datetime(data["date"], errors="coerce")

        if normalize:
            present = [col for col in self.NUMERIC_COLUMNS if col in data]
            if present:
                data[[f"{col}_norm" for col in present]] = MinMaxScaler().fit_transform(data[present])

        return data, {
            "rows_before": before_rows,
            "rows_after": len(data),
            "duplicates_removed": before_rows - len(data),
            "columns": list(data.columns),
        }

    @staticmethod
    def _cap_outliers(series):
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0 or pd.isna(iqr):
            return series
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        return series.clip(lower, upper)

