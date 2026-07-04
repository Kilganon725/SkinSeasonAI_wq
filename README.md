# SkinSeasonAI

基于 Python 的季节变化与皮肤病发病规律分析及可视化预测系统设计与实现。

## Features

- Flask + SQLite web system with user login.
- CSV, Excel, and SQLite data import.
- Automatic column detection and configurable-friendly schema mapping.
- Missing value handling, duplicate removal, outlier capping, and optional normalization.
- Monthly trends, seasonal comparisons, disease distribution, weather statistics, and correlation analysis.
- Plotly line, bar, pie, heatmap, scatter, box, radar, and dashboard charts.
- Linear Regression, Decision Tree, Random Forest, and optional XGBoost models.
- MAE, RMSE, R², model comparison, feature importance, and prediction history.
- PDF and Excel report export.
- Bootstrap 5 responsive UI with dark mode.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open `http://127.0.0.1:5000`.

Default login:

- username: `admin`
- password: `admin123`

## Project Structure

```text
app/          Flask application, routes, database models
data/         Uploaded and processed data
models/       Reserved for serialized model artifacts
services/     Import, cleaning, EDA, visualization, ML, export services
utils/        Constants and column mapping
templates/    Bootstrap pages
static/       CSS and JavaScript
database/     SQLite database
train/        Standalone training scripts
reports/      Exported PDF and Excel reports
docs/         Architecture, API, deployment documentation
datasets/     Local-only original skin disease image datasets, not committed
```

## Dataset Notes

The original image dataset is intentionally not uploaded to GitHub because it is large and should remain a local dataset asset. Put it under `datasets/SkinDisease` when running the project locally.

On first startup, the application scans `datasets/SkinDisease` when that folder exists, maps disease folders into the project disease categories, and creates a reproducible monthly seasonal incidence dataset for demonstration and analysis. If the folder is absent, the application still starts and generates a built-in fallback dataset so the web system, charts, exports, and machine learning pages remain usable.

You can still upload real CSV, Excel, or SQLite incidence data later from the Dataset Management page.

## Documentation

- `docs/ARCHITECTURE.md`
- `docs/API.md`
- `docs/DEPLOYMENT.md`
