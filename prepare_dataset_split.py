import argparse
import random
import shutil
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def collect_images(class_dir: Path):
    images = []
    for path in class_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            images.append(path)
    return images


def split_counts(total: int, train_ratio: float, val_ratio: float):
    train_count = int(total * train_ratio)
    val_count = int(total * val_ratio)
    test_count = total - train_count - val_count
    return train_count, val_count, test_count


def parse_labels(source_dir: Path, labels_arg: str):
    if labels_arg:
        labels = [label.strip() for label in labels_arg.split(",") if label.strip()]
    else:
        labels = [p.name for p in source_dir.iterdir() if p.is_dir()]

    if not labels:
        raise ValueError("Tidak ada label/kelas ditemukan di source directory.")

    return labels


def prepare_output_dirs(output_dir: Path, labels, clear_output: bool):
    if clear_output and output_dir.exists():
        shutil.rmtree(output_dir)

    for split in ["train", "val", "test"]:
        for label in labels:
            (output_dir / split / label).mkdir(parents=True, exist_ok=True)


def transfer_files(files, destination: Path, move_files: bool):
    for file_path in files:
        target_path = destination / file_path.name
        if target_path.exists():
            stem = target_path.stem
            suffix = target_path.suffix
            counter = 1
            while target_path.exists():
                target_path = destination / f"{stem}_{counter}{suffix}"
                counter += 1

        if move_files:
            shutil.move(str(file_path), str(target_path))
        else:
            shutil.copy2(str(file_path), str(target_path))


def split_dataset(source_dir: Path, output_dir: Path, labels, train_ratio, val_ratio, seed, move_files=False, clear_output=False):
    random.seed(seed)

    prepare_output_dirs(output_dir, labels, clear_output)

    grand_total = 0
    print("=== Ringkasan Split Dataset ===")

    for label in labels:
        class_dir = source_dir / label
        if not class_dir.exists() or not class_dir.is_dir():
            print(f"[Lewati] Folder label tidak ditemukan: {class_dir}")
            continue

        images = collect_images(class_dir)
        if not images:
            print(f"[Lewati] Tidak ada gambar pada label: {label}")
            continue

        random.shuffle(images)
        total = len(images)
        train_count, val_count, test_count = split_counts(total, train_ratio, val_ratio)

        train_files = images[:train_count]
        val_files = images[train_count:train_count + val_count]
        test_files = images[train_count + val_count:]

        transfer_files(train_files, output_dir / "train" / label, move_files)
        transfer_files(val_files, output_dir / "val" / label, move_files)
        transfer_files(test_files, output_dir / "test" / label, move_files)

        grand_total += total
        print(
            f"Label '{label}': total={total}, "
            f"train={len(train_files)}, val={len(val_files)}, test={len(test_files)}"
        )

    print(f"Total gambar diproses: {grand_total}")
    print(f"Output: {output_dir}")


def build_parser():
    parser = argparse.ArgumentParser(description="Split dataset gambar ke train/val/test.")
    parser.add_argument("--source-dir", required=True, help="Folder sumber yang berisi subfolder kelas, contoh: raw_dataset")
    parser.add_argument("--output-dir", default="dataset", help="Folder output split, default: dataset")
    parser.add_argument("--labels", default="", help="Daftar label dipisah koma, contoh: drowsy,awake")
    parser.add_argument("--train-ratio", type=float, default=0.7, help="Rasio train, default: 0.7")
    parser.add_argument("--val-ratio", type=float, default=0.15, help="Rasio val, default: 0.15")
    parser.add_argument("--seed", type=int, default=42, help="Seed random, default: 42")
    parser.add_argument("--move", action="store_true", help="Pindahkan file (default copy)")
    parser.add_argument("--clear-output", action="store_true", help="Hapus output-dir sebelum split")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    output_dir = Path(args.output_dir)

    if not source_dir.exists() or not source_dir.is_dir():
        raise ValueError(f"Source directory tidak valid: {source_dir}")

    test_ratio = 1.0 - args.train_ratio - args.val_ratio
    if args.train_ratio <= 0 or args.val_ratio < 0 or test_ratio < 0:
        raise ValueError("Rasio tidak valid. Pastikan train_ratio + val_ratio <= 1.0")

    labels = parse_labels(source_dir, args.labels)

    split_dataset(
        source_dir=source_dir,
        output_dir=output_dir,
        labels=labels,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        seed=args.seed,
        move_files=args.move,
        clear_output=args.clear_output,
    )


if __name__ == "__main__":
    main()
