import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


BACKEND_DIRECTORY = Path(__file__).resolve().parents[2]
UPLOAD_ROOT = BACKEND_DIRECTORY / "uploads"

FILE_WRITE_CHUNK_SIZE_BYTES = 1024 * 1024


async def save_upload_file(
    uploaded_file: UploadFile,
    report_id: int,
    file_category: str,
    extension: str,
) -> str:
    report_directory = UPLOAD_ROOT / str(report_id)
    report_directory.mkdir(parents=True, exist_ok=True)

    generated_filename = (
        f"{file_category}_{uuid4().hex}{extension}"
    )

    storage_key = Path(str(report_id)) / generated_filename
    destination = UPLOAD_ROOT / storage_key

    await uploaded_file.seek(0)

    try:
        with destination.open("wb") as saved_file:
            while True:
                chunk = await uploaded_file.read(
                    FILE_WRITE_CHUNK_SIZE_BYTES
                )

                if not chunk:
                    break

                saved_file.write(chunk)

    except OSError:
        if destination.exists():
            destination.unlink()

        raise

    finally:
        await uploaded_file.seek(0)

    return storage_key.as_posix()


def delete_report_uploads(report_id: int) -> None:
    report_directory = UPLOAD_ROOT / str(report_id)

    if report_directory.exists():
        shutil.rmtree(report_directory)