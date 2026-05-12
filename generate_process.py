import json
import shutil
import subprocess
import time
from pathlib import Path

from reel import text_to_speech_file

from config import IMAGEKIT_UPLOAD_FOLDER
from imagekit_storage import download_file, imagekit_enabled, upload_file_bytes


BASE_DIR = Path(__file__).resolve().parent
JOB_ROOT = BASE_DIR / "data" / "jobs"
WORK_ROOT = BASE_DIR / "runtime" / "work"


def load_manifest(folder_dir: Path) -> dict | None:
    manifest_path = folder_dir / "manifest.json"
    if manifest_path.exists():
        try:
            return json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def text_to_audio(folder_dir: Path, manifest: dict, audio_path: Path) -> None:
    print("TTA-- ", folder_dir.name)
    text = manifest.get("description", "")
    print(text, folder_dir.name)
    text_to_speech_file(text, audio_path)


def write_manifest(folder_dir: Path, manifest: dict) -> None:
    (folder_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def build_work_inputs(folder_dir: Path, manifest: dict) -> Path:
    work_dir = WORK_ROOT / folder_dir.name
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    input_lines = []
    for asset in manifest.get("files", []):
        file_name = asset["name"]
        destination = work_dir / file_name

        if asset.get("storage") == "imagekit" and asset.get("url"):
            download_file(asset["url"], destination)
        else:
            raise ValueError(f"Unsupported asset storage for {file_name}")

        input_lines.append(f"file '{destination.resolve().as_posix()}'\n duration 1\n")

    (work_dir / "input.txt").write_text("".join(input_lines), encoding="utf-8")
    return work_dir


def upload_final_reel(folder: str, mp4_path: Path) -> dict:
    if not imagekit_enabled():
        raise RuntimeError("IMAGEKIT_PRIVATE_KEY is not configured.")

    upload_result = upload_file_bytes(
        mp4_path.read_bytes(),
        f"{folder}.mp4",
        folder=f"{IMAGEKIT_UPLOAD_FOLDER}/reels/{folder}",
    )
    if not upload_result:
        raise RuntimeError(f"ImageKit reel upload failed for {folder}.")

    return {
        "storage": "imagekit",
        "reel_url": upload_result["url"],
        "filePath": upload_result.get("filePath"),
    }


def create_reel(folder_dir: Path, manifest: dict) -> dict:
    work_dir = build_work_inputs(folder_dir, manifest)
    audio_path = work_dir / "audio.mp3"
    text_to_audio(folder_dir, manifest, audio_path)
    command = (
        f'''ffmpeg -f concat -safe 0 -i "{work_dir / 'input.txt'}" '''
        f'''-i "{audio_path}" -vf "scale=1080:1920:force_original_aspect_ratio=decrease,'''
        f'''pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black" -c:v libx264 -c:a aac -shortest -r 30 -pix_fmt yuv420p "{work_dir / 'reel.mp4'}"'''
    )
    subprocess.run(command, shell=True, check=True)
    print("CR-- ", folder_dir.name)

    upload_result = upload_final_reel(folder_dir.name, work_dir / "reel.mp4")
    manifest["status"] = "done"
    manifest["reel"] = upload_result
    write_manifest(folder_dir, manifest)
    (folder_dir / "reel.json").write_text(json.dumps(upload_result, indent=2), encoding="utf-8")
    shutil.rmtree(work_dir, ignore_errors=True)
    return upload_result


if __name__ == "__main__":
    while True:
        print("processing...")
        if not JOB_ROOT.exists():
            time.sleep(3)
            continue

        folders = list(JOB_ROOT.iterdir())
        for folder_dir in folders:
            if not folder_dir.is_dir():
                continue

            manifest = load_manifest(folder_dir)
            if not manifest or manifest.get("status") == "done":
                continue

            create_reel(folder_dir, manifest)
            print("Process generation completed.")

        time.sleep(3)