from app import create_app, db
from services.seed_service import SeedService


def login(client):
    return client.post(
        "/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=True,
    )


def test_core_pages_and_exports(tmp_path):
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'test.sqlite3'}",
        WTF_CSRF_ENABLED=False,
    )
    with app.app_context():
        db.create_all()
        SeedService().ensure_default_data()

    client = app.test_client()
    assert login(client).status_code == 200

    for path in [
        "/",
        "/dataset",
        "/weather",
        "/season",
        "/disease",
        "/image-diagnosis",
        "/prediction",
        "/dashboard",
        "/about",
        "/api/records",
        "/api/charts",
        "/export/excel",
        "/export/pdf",
    ]:
        response = client.get(path)
        assert response.status_code == 200
