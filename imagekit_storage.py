from pathlib import Path

import requests

from config import IMAGEKIT_PRIVATE_KEY


IMAGEKIT_UPLOAD_URL = "https://upload.imagekit.io/api/v1/files/upload"


def imagekit_enabled() -> bool:
    return bool(IMAGEKIT_PRIVATE_KEY)


def upload_file_bytes(file_bytes: bytes, file_name: str, folder: str) -> dict | None:
    if not imagekit_enabled():
        return None

    response = requests.post(
        IMAGEKIT_UPLOAD_URL,
        auth=(IMAGEKIT_PRIVATE_KEY, ""),
        files={"file": (file_name, file_bytes, "application/octet-stream")},
        data={
            "fileName": file_name,
            "folder": folder,
            "useUniqueFileName": "true",
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def upload_file_path(file_path: Path, file_name: str, folder: str) -> dict | None:
    with file_path.open("rb") as file_handle:
        return upload_file_bytes(file_handle.read(), file_name, folder)


def download_file(url: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with destination.open("wb") as file_handle:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file_handle.write(chunk)
    return destination


def remote_file_exists(url: str) -> bool:
    try:
        response = requests.head(url, allow_redirects=True, timeout=20)
        if response.status_code == 405:
            response = requests.get(url, stream=True, timeout=20)
        return response.ok
    except requests.RequestException:
        return False