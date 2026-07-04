import pandas as pd

from utils.constants import WEATHER_COLUMNS


class AnalysisService:
    def __init__(self, frame):
        self.frame = frame.copy()

    def summary(self):
        if self.frame.empty:
            return {}
        numeric = self.frame.select_dtypes(include="number")
        return {
            "rows": int(len(self.frame)),
            "disease_count": int(self.frame["disease"].nunique()) if "disease" in self.frame else 0,
            "total_incidence": float(self.frame["incidence"].sum()) if "incidence" in self.frame else 0,
            "avg_incidence": float(self.frame["incidence"].mean()) if "incidence" in self.frame else 0,
            "numeric_summary": numeric.describe().round(2).to_dict() if not numeric.empty else {},
        }

    def monthly_trend(self):
        return self._group(["month"])

    def seasonal_comparison(self):
        return self._group(["season"])

    def disease_distribution(self):
        return self._group(["disease"])

    def disease_by_season(self):
        if self.frame.empty:
            return pd.DataFrame()
        return self.frame.pivot_table(
            index="season", columns="disease", values="incidence", aggfunc="sum", fill_value=0
        )

    def weather_correlation(self):
        cols = [col for col in WEATHER_COLUMNS + ["incidence", "month"] if col in self.frame]
        if len(cols) < 2:
            return pd.DataFrame()
        return self.frame[cols].corr(numeric_only=True).round(3)

    def weather_statistics(self):
        cols = [col for col in WEATHER_COLUMNS if col in self.frame]
        if not cols:
            return pd.DataFrame()
        return self.frame.groupby("season")[cols].mean(numeric_only=True).round(2)

    def _group(self, columns):
        if self.frame.empty:
            return pd.DataFrame()
        return (
            self.frame.groupby(columns, dropna=False)["incidence"]
            .sum()
            .reset_index()
            .sort_values(columns)
        )

