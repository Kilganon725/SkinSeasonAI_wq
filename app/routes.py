import json
from datetime import datetime
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
from app.models import DiseaseRecord, ImageDiagnosisHistory, PredictionHistory, User
from services.analysis_service import AnalysisService
from services.data_cleaner import DataCleaner
from services.data_importer import DataImporter
from services.export_service import ExportService
from services.image_classifier_service import ImageClassifierService
from services.ml_service import MachineLearningService
from services.seed_service import SeedService
from services.visualization_service import VisualizationService
from utils.constants import DISEASE_CATEGORIES, SEASONS


main_bp = Blueprint("main", __name__)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


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
        user = User.query.filter_by(username=request.form.get("username", "").strip()).first()
        if user and user.check_password(request.form.get("password", "")):
            login_user(user)
            flash("欢迎回来，登录成功。", "success")
            return redirect(url_for("main.home"))
        flash("用户名或密码错误。", "danger")
    return render_template("login.html", auth_mode="login")


@main_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(username) < 3 or len(username) > 32:
            flash("用户名长度需在 3 到 32 个字符之间。", "warning")
            return render_template("login.html", auth_mode="register")
        if len(password) < 6:
            flash("密码至少需要 6 位字符。", "warning")
            return render_template("login.html", auth_mode="register")
        if password != confirm_password:
            flash("两次输入的密码不一致。", "warning")
            return render_template("login.html", auth_mode="register")
        if User.query.filter_by(username=username).first():
            flash("该用户名已被占用，请更换后重试。", "warning")
            return render_template("login.html", auth_mode="register")

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("注册成功，已自动登录。", "success")
        return redirect(url_for("main.home"))

    return render_template("login.html", auth_mode="register")


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


@main_bp.route("/image-diagnosis", methods=["GET", "POST"])
@login_required
def image_diagnosis():
    service = ImageClassifierService()
    result = None
    uploaded_url = None

    if request.method == "POST":
        action = request.form.get("action", "predict")
        if action == "train":
            try:
                max_per_class = int(request.form.get("max_per_class", 80))
                metrics = service.train(max_per_class=max(5, min(max_per_class, 300)))
                flash(
                    f"视觉模型训练完成：{metrics['class_count']} 类，{metrics['sample_count']} 张，"
                    f"accuracy={metrics['accuracy']}，macro_f1={metrics['macro_f1']}。",
                    "success",
                )
            except Exception as exc:
                flash(f"视觉模型训练失败：{exc}", "danger")
            return redirect(url_for("main.image_diagnosis"))

        file = request.files.get("image")
        if not file or not file.filename:
            flash("请选择要识别的皮肤图片。", "warning")
            return redirect(url_for("main.image_diagnosis"))

        suffix = Path(file.filename).suffix.lower()
        if suffix not in IMAGE_EXTENSIONS:
            flash("仅支持 JPG、PNG、BMP、WEBP 图片。", "warning")
            return redirect(url_for("main.image_diagnosis"))

        upload_dir = Path(current_app.config["IMAGE_UPLOAD_FOLDER"])
        upload_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{secure_filename(file.filename)}"
        image_path = upload_dir / filename
        file.save(image_path)
        uploaded_url = url_for("static", filename=f"uploads/diagnosis/{filename}")

        try:
            if not service.model_exists() and service.dataset_available():
                flash("首次使用图像识别，正在基于本地数据集训练轻量视觉模型。", "info")
                service.train(max_per_class=60)
            result = service.predict(image_path)
            history = ImageDiagnosisHistory(
                image_path=f"uploads/diagnosis/{filename}",
                predicted_label=result["label"],
                confidence=result["confidence"],
                top_predictions_json=ImageClassifierService.dumps_top_predictions(result["top_predictions"]),
                model_name=result["model_name"],
            )
            db.session.add(history)
            db.session.commit()
        except Exception as exc:
            flash(f"图像识别失败：{exc}", "danger")

    histories = ImageDiagnosisHistory.query.order_by(ImageDiagnosisHistory.created_at.desc()).limit(12).all()
    return render_template(
        "image_diagnosis.html",
        status=service.status(),
        result=result,
        uploaded_url=uploaded_url,
        histories=histories,
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
