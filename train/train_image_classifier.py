import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.image_classifier_service import ImageClassifierService


def main():
    parser = argparse.ArgumentParser(description="Train the SkinSeasonAI image classifier.")
    parser.add_argument("--max-per-class", type=int, default=80, help="Maximum images sampled per disease class.")
    parser.add_argument("--dataset-root", default=None, help="Path to datasets/SkinDisease.")
    parser.add_argument("--model-path", default=None, help="Output .joblib model path.")
    args = parser.parse_args()

    service = ImageClassifierService(dataset_root=args.dataset_root, model_path=args.model_path)
    metrics = service.train(max_per_class=args.max_per_class)
    print("Image classifier trained successfully.")
    for key, value in metrics.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
