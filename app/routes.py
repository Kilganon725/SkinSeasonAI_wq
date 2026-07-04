import json
from pathlib import Path

import pandas as pd
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.utils import secure_filename

from app import db
from app.models import DiseaseRecord, PredictionHistory, User
from services.analysis_service import AnalysisService
from services.data_cleaner import DataCleaner
from services.data_importer import DataImporter
from services.export_service import ExportService
from services.ml_service import MachineLearningService
from services.seed_service import SeedService
from services.visualization_service import VisualizationService
from utils.constants import DISEASE_CATEGORIES, SEASONS


main_bp = Blueprint("main", __name__)


def records_frame():
    rows = [record.to_dict() for record in DiseaseRecord.query.order_by(DiseaseRecord.year, DiseaseRecord.month).all()]
    return pd.DataFrame(rows)


def dashboard_context():
    frame = records_frame()
    analysis = AnalysisService(frame)
    charts = VisualizationService(frame).all_charts() if not frame.empty else {}
    summary = analysis.summary()
    return frame, analysis, charts, summary


@main_bp.route("/")
@login_required
def home():
    frame, _, charts, summary = dashboard_context()
    recent_predictions = PredictionHistory.query.order_by(PredictionHistory.created_at.desc()).limit(5).all()
    return render_template("home.html", summary=summary, charts=charts, records=frame.tail(8), predictions=recent_predictions)


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    if request.method == "POST":
        user = User.query.filter_by(username=request.form.get("username", "")).first()
        if user and user.check_password(request.form.get("password", "")):
            login_user(user)
            return redirect(url_for("main.home"))
        flash("用户名或密码错误。", "danger")
    return render_template("login.html")


@main_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.login"))


@main_bp.route("/dataset", methods=["GET", "POST"])
@login_required
def dataset_management():
    import_report = None
    if request.method == "POST":
        file = request.files.get("dataset")
        if not file or not file.filename:
            flash("请选择要上传的数据文件。", "warning")
            return redirect(url_for("main.dataset_management"))

        upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
        upload_dir.mkdir(parents=True, exist_ok=True)
        filename = secure_filename(file.filename)
        path = upload_dir / filename
        file.save(path)

        try:
            importer = DataImporter()
            raw = importer.load_file(path, request.form.get("sqlite_table") or None)
            standardized = importer.standardize(raw, source=filename)
            cleaned, import_report = DataCleaner().clean(standardized, normalize=bool(request.form.get("normalize")))
            SeedService().save_records(cleaned)
            flash(f"成功导入 {len(cleaned)} 条记录。", "success")
        except Exception as exc:
            flash(f"导入失败：{exc}", "danger")

    frame = records_frame()
    return render_template(
        "dataset.html",
        records=frame.tail(50),
        import_report=import_report,
        total_records=len(frame),
    )


@main_bp.route("/weather")
@login_required
def weather_analysis():
    frame, analysis, charts, _ = dashboard_context()
    stats = analysis.weather_statistics()
    corr = analysis.weather_correlation()
    return render_template("weather.html", charts=charts, stats=stats, corr=corr)


@main_bp.route("/season")
@login_required
def season_analysis():
    _, analysis, charts, _ = dashboard_context()
    return render_template(
        "season.html",
        charts=charts,
        seasonal=analysis.seasonal_comparison(),
        season_disease=analysis.disease_by_season(),
    )


@main_bp.route("/disease")
@login_required
def disease_analysis():
    _, analysis, charts, _ = dashboard_context()
    return render_template(
        "disease.html",
        charts=charts,
        distribution=analysis.disease_distribution(),
        disease_categories=DISEASE_CATEGORIES,
    )


@main_bp.route("/prediction", methods=["GET", "POST"])
@login_required
def prediction():
    frame = records_frame()
    ml = MachineLearningService(frame)
    _, comparison = ml.train_models()
    prediction_result = None

    if request.method == "POST":
        values = {
            "month": int(request.form.get("month", 1)),
            "season": SEASONS[int(request.form.get("month", 1))],
            "disease": request.form.get("disease", "Eczema"),
            "temperature": float(request.form.get("temperature", 20)),
            "humidity": float(request.form.get("humidity", 60)),
            "rainfall": float(request.form.get("rainfall", 50)),
            "pm25": float(request.form.get("pm25", 35)),
            "uv_index": float(request.form.get("uv_index", 5)),
            "wind_speed": float(request.form.get("wind_speed", 2)),
        }
        prediction_result = ml.predict(values, request.form.get("model_name", "Random Forest"))

    histories = PredictionHistory.query.order_by(PredictionHistory.created_at.desc()).limit(20).all()
    return render_template(
        "prediction.html",
        comparison=comparison,
        result=prediction_result,
        histories=histories,
        disease_categories=DISEASE_CATEGORIES,
    )


@main_bp.route("/dashboard")
@login_required
def dashboard():
    _, _, charts, summary = dashboard_context()
    return render_template("dashboard.html", charts=charts, summary=summary)


@main_bp.route("/about")
@login_required
def about():
    return render_template("about.html")


@main_bp.route("/export/excel")
@login_required
def export_excel():
    path = ExportService().export_excel(records_frame())
    return send_file(path, as_attachment=True)


@main_bp.route("/export/pdf")
@login_required
def export_pdf():
    summary = AnalysisService(records_frame()).summary()
    path = ExportService().export_pdf(summary)
    return send_file(path, as_attachment=True)


@main_bp.route("/api/records")
@login_required
def api_records():
    return {"records": records_frame().to_dict(orient="records")}


@main_bp.route("/api/charts")
@login_required
def api_charts():
    return VisualizationService(records_frame()).all_charts()

