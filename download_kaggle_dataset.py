import argparse
import shutil
from pathlib import Path

import kagglehub


def main():
    parser = argparse.ArgumentParser(description="Download dataset Kaggle ke folder lokal proyek")
    parser.add_argument("--dataset", required=True, help="Contoh: nexuswho/drowsiness-detection")
    parser.add_argument("--output-dir", default="dataset_kaggle", help="Folder output lokal")
    parser.add_argument("--clear-output", action="store_true", help="Hapus output-dir sebelum copy")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    if args.clear_output and output_dir.exists():
        shutil.rmtree(output_dir)

    cache_path = Path(kagglehub.dataset_download(args.dataset))
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(cache_path, output_dir, dirs_exist_ok=True)

    print(f"Dataset cache path : {cache_path}")
    print(f"Dataset local path : {output_dir.resolve()}")


if __name__ == "__main__":
    main()
