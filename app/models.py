from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class DiseaseRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=True)
    year = db.Column(db.Integer, nullable=True)
    month = db.Column(db.Integer, nullable=True)
    season = db.Column(db.String(20), nullable=True)
    disease = db.Column(db.String(80), nullable=False)
    incidence = db.Column(db.Float, nullable=False, default=0)
    temperature = db.Column(db.Float, nullable=True)
    humidity = db.Column(db.Float, nullable=True)
    rainfall = db.Column(db.Float, nullable=True)
    pm25 = db.Column(db.Float, nullable=True)
    uv_index = db.Column(db.Float, nullable=True)
    wind_speed = db.Column(db.Float, nullable=True)
    source = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "year": self.year,
            "month": self.month,
            "season": self.season,
            "disease": self.disease,
            "incidence": self.incidence,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "rainfall": self.rainfall,
            "pm25": self.pm25,
            "uv_index": self.uv_index,
            "wind_speed": self.wind_speed,
            "source": self.source,
        }


class PredictionHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(80), nullable=False)
    disease = db.Column(db.String(80), nullable=True)
    input_json = db.Column(db.Text, nullable=False)
    predicted_incidence = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

