from __future__ import annotations

import argparse
import io
import zipfile
from pathlib import Path

import requests

from common import (
    DATASET_NAME,
    DATASET_URL,
    RAW_ARCHIVE_NAME,
    RAW_CSV_NAME,
    RAW_DATA_DIR,
    ensure_directories,
)


def download_dataset(output_dir: Path, force: bool) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / RAW_ARCHIVE_NAME
    csv_path = output_dir / RAW_CSV_NAME

    if archive_path.exists() and csv_path.exists() and not force:
        return archive_path, csv_path

    response = requests.get(DATASET_URL, timeout=60)
    response.raise_for_status()
    archive_path.write_bytes(response.content)

    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        members = archive.namelist()
        if RAW_CSV_NAME not in members:
            raise FileNotFoundError(
                f"Expected {RAW_CSV_NAME} inside archive, found: {members}"
            )
        archive.extract(RAW_CSV_NAME, path=output_dir)

    return archive_path, csv_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download the public AI4I predictive maintenance dataset."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=RAW_DATA_DIR,
        help="Directory for raw dataset files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Redownload and overwrite the raw dataset files.",
    )
    args = parser.parse_args()

    ensure_directories()
    archive_path, csv_path = download_dataset(args.output_dir, force=args.force)

    print(f"Downloaded {DATASET_NAME}")
    print(f"Archive: {archive_path}")
    print(f"CSV: {csv_path}")


if __name__ == "__main__":
    main()

