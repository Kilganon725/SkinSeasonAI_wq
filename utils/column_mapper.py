import re


class ColumnMapper:
    """Map heterogeneous uploaded datasets into the system schema."""

    CANDIDATES = {
        "date": ["date", "datetime", "record_date", "日期", "时间"],
        "year": ["year", "年份"],
        "month": ["month", "月份", "月"],
        "season": ["season", "季节"],
        "disease": ["disease", "disease_type", "diagnosis", "category", "病种", "疾病", "皮肤病"],
        "incidence": ["incidence", "cases", "case_count", "count", "发病数", "病例数", "数量"],
        "temperature": ["temperature", "temp", "avg_temp", "气温", "温度"],
        "humidity": ["humidity", "湿度"],
        "rainfall": ["rainfall", "rain", "precipitation", "降雨", "降水"],
        "pm25": ["pm25", "pm2.5", "pm_2_5", "空气颗粒物"],
        "uv_index": ["uv", "uv_index", "紫外线", "紫外线指数"],
        "wind_speed": ["wind", "wind_speed", "风速"],
    }

    @staticmethod
    def normalize_name(name):
        return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", str(name).lower())

    def detect(self, columns):
        normalized = {self.normalize_name(col): col for col in columns}
        mapping = {}
        for target, candidates in self.CANDIDATES.items():
            for candidate in candidates:
                key = self.normalize_name(candidate)
                if key in normalized:
                    mapping[target] = normalized[key]
                    break
        return mapping

