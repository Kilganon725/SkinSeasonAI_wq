# SkinSeasonAI Project Architecture

SkinSeasonAI uses a layered Flask architecture.

## Layers

- `app/`: Flask factory, database models, authentication, routes.
- `services/`: data import, cleaning, analysis, visualization, machine learning, report export, seed data generation.
- `utils/`: constants and automatic column mapping.
- `templates/`: Bootstrap 5 pages.
- `static/`: CSS and browser-side Plotly rendering helpers.
- `database/`: SQLite database generated at runtime.
- `data/raw/`: uploaded source files.
- `data/processed/`: cleaned and generated datasets.
- `reports/`: exported PDF and Excel reports.
- `train/`: standalone model training entry points.

## Data Flow

1. CSV, Excel, or SQLite file is uploaded on the Dataset Management page.
2. `DataImporter` reads the file and `ColumnMapper` detects known fields.
3. `DataCleaner` removes duplicates, fills missing values, caps outliers, and can create normalized features.
4. Clean records are stored in SQLite as `DiseaseRecord`.
5. `AnalysisService` aggregates data by month, season, disease, and weather variables.
6. `VisualizationService` produces Plotly JSON for the UI.
7. `MachineLearningService` trains regression models and stores predictions in `PredictionHistory`.
8. `ExportService` exports Excel and PDF reports.

## Default Data

When no records exist, `SeedService` reads the local image dataset under `datasets/SkinDisease` if present, maps available classes into the required disease categories, and creates a reproducible monthly seasonal incidence dataset. The `datasets/` directory is intentionally ignored by Git because the dataset is large. If no local dataset is present, `SeedService` creates fallback demonstration records so the system remains runnable after cloning.
