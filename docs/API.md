# SkinSeasonAI API Documentation

All API routes require login.

## `GET /api/records`

Returns all disease incidence records from SQLite.

Response:

```json
{
  "records": [
    {
      "date": "2025-01-01",
      "year": 2025,
      "month": 1,
      "season": "Winter",
      "disease": "Eczema",
      "incidence": 144,
      "temperature": 2,
      "humidity": 54,
      "rainfall": 18,
      "pm25": 72,
      "uv_index": 2,
      "wind_speed": 2.2
    }
  ]
}
```

## `GET /api/charts`

Returns Plotly JSON strings for all dashboard charts.

Keys:

- `line`
- `bar`
- `pie`
- `heatmap`
- `scatter`
- `box`
- `radar`
- `season_disease`

## Web Endpoints

- `/`: system overview.
- `/dataset`: upload and clean datasets.
- `/weather`: weather factor analysis.
- `/season`: seasonal analysis.
- `/disease`: disease category analysis.
- `/prediction`: model comparison and prediction.
- `/image-diagnosis`: train local image model and classify uploaded skin images.
- `/dashboard`: interactive visualization dashboard.
- `/export/excel`: export Excel report.
- `/export/pdf`: export PDF report.
