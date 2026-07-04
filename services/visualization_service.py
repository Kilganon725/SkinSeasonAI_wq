import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder

from services.analysis_service import AnalysisService
from utils.constants import WEATHER_COLUMNS


class VisualizationService:
    def __init__(self, frame):
        self.frame = frame.copy()
        self.analysis = AnalysisService(frame)

    def all_charts(self):
        return {
            "line": self.line_monthly(),
            "bar": self.bar_season(),
            "pie": self.pie_disease(),
            "heatmap": self.heatmap_correlation(),
            "scatter": self.scatter_weather(),
            "box": self.box_season(),
            "radar": self.radar_weather(),
            "season_disease": self.season_disease_heatmap(),
        }

    def line_monthly(self):
        data = self.analysis.monthly_trend()
        fig = px.line(data, x="month", y="incidence", markers=True, title="月度发病趋势")
        return self._json(fig)

    def bar_season(self):
        data = self.analysis.seasonal_comparison()
        fig = px.bar(data, x="season", y="incidence", color="season", title="季节发病对比")
        return self._json(fig)

    def pie_disease(self):
        data = self.analysis.disease_distribution()
        fig = px.pie(data, names="disease", values="incidence", title="疾病类别占比")
        return self._json(fig)

    def heatmap_correlation(self):
        corr = self.analysis.weather_correlation()
        fig = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale="RdBu_r", title="相关性热力图")
        return self._json(fig)

    def scatter_weather(self):
        x_col = "temperature" if "temperature" in self.frame else "month"
        fig = px.scatter(
            self.frame,
            x=x_col,
            y="incidence",
            color="disease" if "disease" in self.frame else None,
            size="uv_index" if "uv_index" in self.frame else None,
            title="气象因素与发病散点图",
        )
        return self._json(fig)

    def box_season(self):
        fig = px.box(self.frame, x="season", y="incidence", color="season", title="季节发病箱线图")
        return self._json(fig)

    def radar_weather(self):
        stats = self.analysis.weather_statistics()
        fig = go.Figure()
        if not stats.empty:
            cols = [col for col in WEATHER_COLUMNS if col in stats.columns]
            normalized = stats[cols].copy()
            for col in cols:
                min_v = normalized[col].min()
                max_v = normalized[col].max()
                normalized[col] = 0 if max_v == min_v else (normalized[col] - min_v) / (max_v - min_v)
            for season, row in normalized.iterrows():
                fig.add_trace(go.Scatterpolar(r=row.values, theta=cols, fill="toself", name=str(season)))
        fig.update_layout(title="季节气象特征雷达图", polar={"radialaxis": {"visible": True, "range": [0, 1]}})
        return self._json(fig)

    def season_disease_heatmap(self):
        pivot = self.analysis.disease_by_season()
        fig = px.imshow(pivot, text_auto=True, aspect="auto", title="疾病-季节发病热力图")
        return self._json(fig)

    @staticmethod
    def _json(fig):
        return json.dumps(fig, cls=PlotlyJSONEncoder)

