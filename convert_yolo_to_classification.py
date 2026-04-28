import argparse
import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path


IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def parse_class_map(class_map_text: str):
    class_map = {}
    for part in class_map_text.split(","):
        item = part.strip()
        if not item:
            continue
        if ":" not in item:
            raise ValueError(f"Format class-map salah: '{item}'. Gunakan contoh 0:microsleep")
        idx_text, name = item.split(":", 1)
        idx = int(idx_text.strip())
        label_name = name.strip()
        if not label_name:
            raise ValueError(f"Nama kelas kosong untuk index {idx}")
        class_map[idx] = label_name

    if not class_map:
        raise ValueError("class-map kosong")
    return class_map


def find_image_for_label(images_dir: Path, stem: str):
    for ext in IMAGE_EXTS:
        candidate = images_dir / f"{stem}{ext}"
        if candidate.exists():
            return candidate

    matches = list(images_dir.glob(f"{stem}.*"))
    for path in matches:
        if path.suffix.lower() in IMAGE_EXTS:
            return path
    return None


def read_main_class(label_file: Path):
    lines = [line.strip() for line in label_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return None

    counts = Counter()
    for line in lines:
        parts = line.split()
        if not parts:
            continue
        try:
            cls_id = int(float(parts[0]))
        except ValueError:
            continue
        counts[cls_id] += 1

    if not counts:
        return None
    return counts.most_common(1)[0][0]


def collect_samples(source_split_dir: Path, class_map: dict[int, str]):
    labels_dir = source_split_dir / "labels"
    images_dir = source_split_dir / "images"

    if not labels_dir.exists() or not images_dir.exists():
        return None, 0

    samples = []
    skipped = 0

    for label_file in sorted(labels_dir.glob("*.txt")):
        stem = label_file.stem
        image_path = find_image_for_label(images_dir, stem)
        if image_path is None:
            skipped += 1
            continue

        cls_id = read_main_class(label_file)
        if cls_id is None:
            skipped += 1
            continue

        class_name = class_map.get(cls_id)
        if class_name is None:
            skipped += 1
            continue

        samples.append((image_path, class_name))

    return samples, skipped


def unique_target_path(target_dir: Path, image_path: Path):
    target_file = target_dir / image_path.name
    if not target_file.exists():
        return target_file

    counter = 1
    while True:
        candidate = target_dir / f"{image_path.stem}_{counter}{image_path.suffix.lower()}"
        if not candidate.exists():
            return candidate
        counter += 1


def copy_samples(samples, output_split_dir: Path):
    copied = 0
    per_class = defaultdict(int)

    for image_path, class_name in samples:
        target_dir = output_split_dir / class_name
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = unique_target_path(target_dir, image_path)
        shutil.copy2(image_path, target_file)
        copied += 1
        per_class[class_name] += 1

    return copied, dict(per_class)


def stratified_train_val_split(samples, val_ratio: float, seed: int):
    grouped = defaultdict(list)
    for sample in samples:
        grouped[sample[1]].append(sample)

    rng = random.Random(seed)
    train_samples = []
    val_samples = []

    for class_samples in grouped.values():
        rng.shuffle(class_samples)
        if len(class_samples) <= 1:
            train_samples.extend(class_samples)
            continue

        val_count = int(round(len(class_samples) * val_ratio))
        val_count = max(1, min(val_count, len(class_samples) - 1))
        val_samples.extend(class_samples[:val_count])
        train_samples.extend(class_samples[val_count:])

    rng.shuffle(train_samples)
    rng.shuffle(val_samples)
    return train_samples, val_samples


def main():
    parser = argparse.ArgumentParser(description="Konversi dataset YOLO ke format klasifikasi folder-per-class")
    parser.add_argument("--source-dir", required=True, help="Folder sumber YOLO (berisi train/valid/test)")
    parser.add_argument("--output-dir", required=True, help="Folder output klasifikasi")
    parser.add_argument(
        "--class-map",
        required=True,
        help="Mapping kelas YOLO. Contoh: 0:microsleep,1:neutral,2:yawning",
    )
    parser.add_argument("--val-ratio", type=float, default=0.2, help="Proporsi validation dari train bila valid tidak punya labels")
    parser.add_argument("--seed", type=int, default=42, help="Seed random untuk split train/val")
    parser.add_argument("--clear-output", action="store_true", help="Hapus isi output-dir sebelum konversi")

    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    output_dir = Path(args.output_dir)
    class_map = parse_class_map(args.class_map)

    if not source_dir.exists():
        raise FileNotFoundError(f"source-dir tidak ditemukan: {source_dir}")

    if args.clear_output and output_dir.exists():
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    train_samples, train_skipped = collect_samples(source_dir / "train", class_map)
    if train_samples is None:
        raise FileNotFoundError("Folder train tidak valid: butuh subfolder images dan labels")

    valid_samples, valid_skipped = collect_samples(source_dir / "valid", class_map)
    test_samples, test_skipped = collect_samples(source_dir / "test", class_map)

    total_skipped = train_skipped + valid_skipped + test_skipped

    if valid_samples is None or len(valid_samples) == 0:
        print("Split valid tidak punya labels. Membuat validation split dari train.")
        train_samples, val_samples = stratified_train_val_split(train_samples, args.val_ratio, args.seed)
    else:
        val_samples = valid_samples

    train_copied, train_per_class = copy_samples(train_samples, output_dir / "train")
    val_copied, val_per_class = copy_samples(val_samples, output_dir / "val")
    test_copied, test_per_class = copy_samples(test_samples or [], output_dir / "test")

    total_copied = train_copied + val_copied + test_copied

    print(f"[train -> train] copied={train_copied}")
    for class_name, count in sorted(train_per_class.items()):
        print(f"  - {class_name}: {count}")

    print(f"[valid -> val] copied={val_copied}")
    for class_name, count in sorted(val_per_class.items()):
        print(f"  - {class_name}: {count}")

    print(f"[test -> test] copied={test_copied}")
    for class_name, count in sorted(test_per_class.items()):
        print(f"  - {class_name}: {count}")

    print(f"Selesai. Total copied={total_copied}, total skipped={total_skipped}")


if __name__ == "__main__":
    main()
