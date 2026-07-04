# Deployment Guide

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open `http://127.0.0.1:5000`.

Default account:

- username: `admin`
- password: `admin123`

## Production

```bash
export SECRET_KEY="replace-with-a-strong-secret"
gunicorn "run:app" --bind 0.0.0.0:8000 --workers 2
```

For a server deployment, place Nginx in front of Gunicorn and persist these folders:

- `database/`
- `data/`
- `reports/`

## Dataset Format

The importer automatically detects common English and Chinese column names for:

- date, year, month, season
- disease
- incidence or case count
- temperature, humidity, rainfall, PM2.5, UV index, wind speed

