import argparse
import json
from pathlib import Path

import numpy as np
import tensorflow as tf


def safe_divide(numerator, denominator):
    return float(numerator) / float(denominator) if denominator != 0 else 0.0


def compute_metrics(y_true, y_pred, class_names):
    n_classes = len(class_names)
    cm = np.zeros((n_classes, n_classes), dtype=np.int64)

    for t, p in zip(y_true, y_pred):
        cm[int(t), int(p)] += 1

    precision_per_class = []
    recall_per_class = []
    f1_per_class = []
    support_per_class = []

    for i in range(n_classes):
        tp = cm[i, i]
        fp = cm[:, i].sum() - tp
        fn = cm[i, :].sum() - tp
        support = cm[i, :].sum()

        precision = safe_divide(tp, tp + fp)
        recall = safe_divide(tp, tp + fn)
        f1 = safe_divide(2 * precision * recall, precision + recall) if (precision + recall) > 0 else 0.0

        precision_per_class.append(precision)
        recall_per_class.append(recall)
        f1_per_class.append(f1)
        support_per_class.append(int(support))

    total_support = int(np.sum(support_per_class))
    correct = int(np.trace(cm))
    accuracy = safe_divide(correct, total_support)

    macro_precision = float(np.mean(precision_per_class)) if n_classes > 0 else 0.0
    macro_recall = float(np.mean(recall_per_class)) if n_classes > 0 else 0.0
    macro_f1 = float(np.mean(f1_per_class)) if n_classes > 0 else 0.0

    weighted_precision = safe_divide(np.sum(np.array(precision_per_class) * np.array(support_per_class)), total_support)
    weighted_recall = safe_divide(np.sum(np.array(recall_per_class) * np.array(support_per_class)), total_support)
    weighted_f1 = safe_divide(np.sum(np.array(f1_per_class) * np.array(support_per_class)), total_support)

    return {
        "confusion_matrix": cm.tolist(),
        "per_class": [
            {
                "class": class_names[i],
                "precision": precision_per_class[i],
                "recall": recall_per_class[i],
                "f1": f1_per_class[i],
                "support": support_per_class[i],
            }
            for i in range(n_classes)
        ],
        "accuracy": accuracy,
        "macro_avg": {
            "precision": macro_precision,
            "recall": macro_recall,
            "f1": macro_f1,
        },
        "weighted_avg": {
            "precision": weighted_precision,
            "recall": weighted_recall,
            "f1": weighted_f1,
        },
        "total_samples": total_support,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate precision/recall/f1 for trained Keras model")
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--test-dir", required=True)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--output-json", default="metrics_report.json")
    args = parser.parse_args()

    model_path = Path(args.model_path)
    if not model_path.exists():
        raise FileNotFoundError(f"Model tidak ditemukan: {model_path}")

    meta_path = model_path.with_suffix(".json")
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata tidak ditemukan: {meta_path}")

    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    class_names = metadata["class_names"]
    image_size = tuple(metadata["image_size"])

    test_ds = tf.keras.utils.image_dataset_from_directory(
        args.test_dir,
        image_size=image_size,
        batch_size=args.batch_size,
        label_mode="int",
        shuffle=False,
    )

    model = tf.keras.models.load_model(model_path)

    y_true_batches = []
    for _, labels in test_ds:
        y_true_batches.append(labels.numpy())
    y_true = np.concatenate(y_true_batches, axis=0)

    y_prob = model.predict(test_ds, verbose=1)
    y_pred = np.argmax(y_prob, axis=1)

    metrics = compute_metrics(y_true, y_pred, class_names)

    print("\n=== Classification Metrics ===")
    print(f"Total samples: {metrics['total_samples']}")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(
        "Macro avg -> "
        f"Precision: {metrics['macro_avg']['precision']:.4f}, "
        f"Recall: {metrics['macro_avg']['recall']:.4f}, "
        f"F1: {metrics['macro_avg']['f1']:.4f}"
    )
    print(
        "Weighted avg -> "
        f"Precision: {metrics['weighted_avg']['precision']:.4f}, "
        f"Recall: {metrics['weighted_avg']['recall']:.4f}, "
        f"F1: {metrics['weighted_avg']['f1']:.4f}"
    )

    print("\nPer class:")
    for item in metrics["per_class"]:
        print(
            f"- {item['class']}: "
            f"precision={item['precision']:.4f}, "
            f"recall={item['recall']:.4f}, "
            f"f1={item['f1']:.4f}, "
            f"support={item['support']}"
        )

    output_path = Path(args.output_json)
    output_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"\nLaporan metrics tersimpan: {output_path.resolve()}")


if __name__ == "__main__":
    main()
