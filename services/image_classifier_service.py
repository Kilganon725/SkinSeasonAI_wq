import json
import random
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config import Config


class ImageClassifierService:
    """Lightweight skin disease image classifier based on classical visual features."""

    MODEL_NAME = "Skin Image RandomForest"
    IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    DISEASE_DESCRIPTIONS = {
        "Acne": "痤疮，常见于面部、胸背部，与皮脂分泌、毛囊堵塞和炎症相关。",
        "Eczema": "湿疹，常表现为红斑、丘疹、瘙痒和渗出，易受季节和湿度影响。",
        "Psoriasis": "银屑病，常见鳞屑性红斑，可反复发作。",
        "Tinea": "癣/真菌感染，常见环形皮损、脱屑和瘙痒。",
        "Candidiasis": "念珠菌感染，多见于潮湿皱褶部位。",
        "Vitiligo": "白癜风，表现为边界较清楚的色素脱失斑。",
        "Warts": "疣，通常与 HPV 感染相关，表面可粗糙角化。",
        "SkinCancer": "皮肤肿瘤相关类别，需要谨慎对待并建议专业评估。",
        "Unknown_Normal": "正常或未知类别，模型认为图像不明显属于训练集疾病表现。",
    }
    HIGH_RISK_LABELS = {"SkinCancer", "Actinic_Keratosis"}

    def __init__(self, dataset_root=None, model_path=None):
        self.dataset_root = Path(dataset_root or Config.DATASET_IMAGE_ROOT)
        self.model_path = Path(model_path or Config.IMAGE_MODEL_PATH)
        self.bundle = None

    def model_exists(self):
        return self.model_path.exists()

    def dataset_available(self):
        train_dir = self.dataset_root / "train"
        return train_dir.exists() and any(path.is_dir() for path in train_dir.iterdir())

    def load(self):
        if self.bundle is None and self.model_exists():
            self.bundle = joblib.load(self.model_path)
        return self.bundle

    def status(self):
        bundle = self.load() if self.model_exists() else None
        labels = self.available_labels()
        return {
            "model_exists": self.model_exists(),
            "dataset_available": self.dataset_available(),
            "model_path": str(self.model_path),
            "label_count": len(labels),
            "labels": labels,
            "metrics": bundle.get("metrics", {}) if bundle else {},
        }

    def available_labels(self):
        train_dir = self.dataset_root / "train"
        if not train_dir.exists():
            return []
        return sorted(path.name for path in train_dir.iterdir() if path.is_dir())

    def train(self, max_per_class=80, random_state=42):
        samples = self._collect_samples(max_per_class=max_per_class, random_state=random_state)
        if len(samples) < 2:
            raise ValueError("没有找到足够的图片样本，无法训练图像识别模型。")

        features = []
        labels = []
        skipped = 0
        for image_path, label in samples:
            try:
                features.append(self.extract_features(image_path))
                labels.append(label)
            except (OSError, UnidentifiedImageError, ValueError):
                skipped += 1

        if len(set(labels)) < 2:
            raise ValueError("至少需要两个疾病类别才能训练图像识别模型。")

        x = np.vstack(features)
        y = np.array(labels)
        stratify = y if min(np.bincount(np.unique(y, return_inverse=True)[1])) >= 2 else None
        x_train, x_test, y_train, y_test = train_test_split(
            x, y, test_size=0.22, random_state=random_state, stratify=stratify
        )

        pipeline = Pipeline(
            [
                ("scale", StandardScaler()),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=180,
                        max_depth=None,
                        min_samples_leaf=2,
                        n_jobs=-1,
                        class_weight="balanced_subsample",
                        random_state=random_state,
                    ),
                ),
            ]
        )
        pipeline.fit(x_train, y_train)
        pred = pipeline.predict(x_test)
        report = classification_report(y_test, pred, output_dict=True, zero_division=0)
        metrics = {
            "accuracy": round(float(accuracy_score(y_test, pred)), 4),
            "sample_count": int(len(y)),
            "train_count": int(len(y_train)),
            "test_count": int(len(y_test)),
            "class_count": int(len(set(y))),
            "skipped_images": int(skipped),
            "max_per_class": int(max_per_class),
            "trained_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "macro_f1": round(float(report["macro avg"]["f1-score"]), 4),
        }
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self.bundle = {
            "pipeline": pipeline,
            "labels": sorted(set(y)),
            "metrics": metrics,
            "model_name": self.MODEL_NAME,
            "feature_version": "histogram-thumbnail-gradient-v1",
        }
        joblib.dump(self.bundle, self.model_path)
        return metrics

    def predict(self, image_path, top_k=3):
        bundle = self.load()
        if not bundle:
            raise FileNotFoundError("图像识别模型尚未训练，请先点击“训练视觉模型”。")

        feature = self.extract_features(image_path).reshape(1, -1)
        pipeline = bundle["pipeline"]
        classes = list(pipeline.classes_)
        if hasattr(pipeline, "predict_proba"):
            probabilities = pipeline.predict_proba(feature)[0]
        else:
            predicted = pipeline.predict(feature)[0]
            probabilities = np.array([1.0 if label == predicted else 0.0 for label in classes])

        ranked = sorted(zip(classes, probabilities), key=lambda item: item[1], reverse=True)[:top_k]
        top_predictions = [
            {
                "label": str(label),
                "confidence": round(float(probability), 4),
                "percent": round(float(probability) * 100, 2),
                "description": self.describe(str(label)),
                "high_risk": str(label) in self.HIGH_RISK_LABELS,
            }
            for label, probability in ranked
        ]
        best = top_predictions[0]
        return {
            "label": best["label"],
            "confidence": best["confidence"],
            "percent": best["percent"],
            "description": best["description"],
            "high_risk": best["high_risk"],
            "top_predictions": top_predictions,
            "model_name": bundle.get("model_name", self.MODEL_NAME),
            "metrics": bundle.get("metrics", {}),
        }

    def describe(self, label):
        return self.DISEASE_DESCRIPTIONS.get(label, f"{label} 类别，来自本地图片数据集的训练标签。")

    def _collect_samples(self, max_per_class, random_state):
        rng = random.Random(random_state)
        train_dir = self.dataset_root / "train"
        samples = []
        for class_dir in sorted(path for path in train_dir.iterdir() if path.is_dir()):
            images = [path for path in class_dir.iterdir() if path.suffix.lower() in self.IMAGE_SUFFIXES]
            rng.shuffle(images)
            samples.extend((path, class_dir.name) for path in images[:max_per_class])
        rng.shuffle(samples)
        return samples

    @classmethod
    def extract_features(cls, image_path):
        image = Image.open(image_path)
        image = ImageOps.exif_transpose(image).convert("RGB")
        image = ImageOps.fit(image, (96, 96), method=Image.Resampling.LANCZOS)
        rgb = np.asarray(image, dtype=np.float32) / 255.0

        hist_features = []
        for channel in range(3):
            hist, _ = np.histogram(rgb[:, :, channel], bins=18, range=(0, 1), density=True)
            hist_features.append(hist.astype(np.float32))

        small = Image.fromarray((rgb * 255).astype(np.uint8)).convert("L").resize((32, 32), Image.Resampling.LANCZOS)
        gray = np.asarray(small, dtype=np.float32) / 255.0
        grad_x = np.abs(np.diff(gray, axis=1))
        grad_y = np.abs(np.diff(gray, axis=0))
        gradient_stats = np.array(
            [
                grad_x.mean(),
                grad_x.std(),
                grad_y.mean(),
                grad_y.std(),
                gray.mean(),
                gray.std(),
                gray.min(),
                gray.max(),
            ],
            dtype=np.float32,
        )

        channel_stats = np.concatenate(
            [
                rgb.mean(axis=(0, 1)),
                rgb.std(axis=(0, 1)),
                rgb.min(axis=(0, 1)),
                rgb.max(axis=(0, 1)),
            ]
        ).astype(np.float32)

        return np.concatenate([*hist_features, gray.flatten(), gradient_stats, channel_stats]).astype(np.float32)

    @staticmethod
    def dumps_top_predictions(top_predictions):
        return json.dumps(top_predictions, ensure_ascii=False)
