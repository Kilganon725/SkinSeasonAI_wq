import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.routes import records_frame
from services.ml_service import MachineLearningService


def main():
    app = create_app()
    with app.app_context():
        _, comparison = MachineLearningService(records_frame()).train_models()
        print(comparison)


if __name__ == "__main__":
    main()
