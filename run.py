from app import create_app, db
from services.seed_service import SeedService


app = create_app()


with app.app_context():
    db.create_all()
    SeedService().ensure_default_data()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

