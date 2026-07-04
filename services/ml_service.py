import json
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeRegressor

try:
    from xgboost import XGBRegressor
except Exception:
    XGBRegressor = None

from app import db
from app.models import PredictionHistory


@dataclass
class ModelResult:
    name: str
    mae: float
    rmse: float
    r2: float
    feature_importance: list


class MachineLearningService:
    FEATURES = ["month", "season", "disease", "temperature", "humidity", "rainfall", "pm25", "uv_index", "wind_speed"]

    def __init__(self, frame):
        self.frame = frame.copy()
        self.models = {}

    def train_models(self):
        data = self._prepare_frame(self.frame)
        if len(data) < 8:
            return {}, []

        x = data[self.FEATURES]
        y = data["incidence"]
        test_size = 0.25 if len(data) >= 20 else 0.3
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=test_size, random_state=42)

        candidates = {
            "Linear Regression": LinearRegression(),
            "Decision Tree": DecisionTreeRegressor(max_depth=6, random_state=42),
            "Random Forest": RandomForestRegressor(n_estimators=160, random_state=42),
        }
        if XGBRegressor is not None:
            candidates["XGBoost"] = XGBRegressor(
                n_estimators=120,
                max_depth=3,
                learning_rate=0.08,
                objective="reg:squarederror",
                random_state=42,
            )

        results = []
        for name, estimator in candidates.items():
            pipeline = Pipeline([("preprocess", self._preprocessor()), ("model", estimator)])
            pipeline.fit(x_train, y_train)
            pred = pipeline.predict(x_test)
            self.models[name] = pipeline
            results.append(
                ModelResult(
                    name=name,
                    mae=round(float(mean_absolute_error(y_test, pred)), 3),
                    rmse=round(float(np.sqrt(mean_squared_error(y_test, pred))), 3),
                    r2=round(float(r2_score(y_test, pred)), 3),
                    feature_importance=self._feature_importance(pipeline),
                )
            )
        best = sorted(results, key=lambda item: (item.rmse, -item.r2))[0].name
        return self.models, {"best_model": best, "results": [item.__dict__ for item in results]}

    def predict(self, values, model_name="Random Forest"):
        if not self.models:
            self.train_models()
        if model_name not in self.models:
            model_name = next(iter(self.models))
        row = self._prepare_frame(pd.DataFrame([values]))[self.FEATURES]
        prediction = float(self.models[model_name].predict(row)[0])
        risk = self.risk_level(prediction)
        history = PredictionHistory(
            model_name=model_name,
            disease=values.get("disease"),
            input_json=json.dumps(values, ensure_ascii=False),
            predicted_incidence=prediction,
            risk_level=risk,
        )
        db.session.add(history)
        db.session.commit()
        return {"prediction": round(prediction, 2), "risk_level": risk, "model_name": model_name}

    def risk_level(self, value):
        q1 = self.frame["incidence"].quantile(0.33)
        q2 = self.frame["incidence"].quantile(0.66)
        if value <= q1:
            return "Low"
        if value <= q2:
            return "Medium"
        return "High"

    def _prepare_frame(self, frame):
        data = frame.copy()
        defaults = {
            "month": 1,
            "season": "Spring",
            "disease": "Eczema",
            "temperature": 20,
            "humidity": 60,
            "rainfall": 50,
            "pm25": 35,
            "uv_index": 5,
            "wind_speed": 2,
            "incidence": 0,
        }
        for col, value in defaults.items():
            if col not in data:
                data[col] = value
            data[col] = data[col].fillna(value)
        for col in ["month", "temperature", "humidity", "rainfall", "pm25", "uv_index", "wind_speed", "incidence"]:
            data[col] = pd.to_numeric(data[col], errors="coerce").fillna(defaults[col])
        return data

    def _preprocessor(self):
        numeric = ["month", "temperature", "humidity", "rainfall", "pm25", "uv_index", "wind_speed"]
        categorical = ["season", "disease"]
        return ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), numeric),
                ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
            ]
        )

    def _feature_importance(self, pipeline):
        model = pipeline.named_steps["model"]
        names = list(pipeline.named_steps["preprocess"].get_feature_names_out())
        if hasattr(model, "feature_importances_"):
            values = model.feature_importances_
        elif hasattr(model, "coef_"):
            values = np.abs(np.ravel(model.coef_))
        else:
            return []
        pairs = sorted(zip(names, values), key=lambda item: item[1], reverse=True)[:12]
        return [{"feature": name, "importance": round(float(value), 4)} for name, value in pairs]

