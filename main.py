from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import uuid
import threading
import time

from flask import Flask, abort, jsonify, render_template, request
from werkzeug.utils import secure_filename

from config import IMAGEKIT_UPLOAD_FOLDER
from imagekit_storage import imagekit_enabled, remote_file_exists, upload_file_bytes


app = Flask(__name__)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

BASE_DIR = Path(__file__).resolve().parent
JOB_ROOT = BASE_DIR / "data" / "jobs"
JOB_ROOT.mkdir(parents=True, exist_ok=True)


def start_generator_process() -> None:
    generator_script = BASE_DIR / "generate_process.py"
    subprocess.Popen([sys.executable, str(generator_script)], cwd=str(BASE_DIR))


def load_reels() -> list[dict]:
    reels: list[dict] = []

    for reel_meta in sorted(JOB_ROOT.glob("*/reel.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            data = json.loads(reel_meta.read_text(encoding="utf-8"))
        except Exception:
            continue

        reel_url = data.get("reel_url")
        if reel_url and remote_file_exists(reel_url):
            reels.append(
                {
                    "url": reel_url,
                    "folder": reel_meta.parent.name,
                    "source": data.get("storage", "imagekit"),
                }
            )
        elif reel_url:
            try:
                reel_meta.unlink(missing_ok=True)
            except TypeError:
                if reel_meta.exists():
                    reel_meta.unlink()

    return reels


def get_reels_payload() -> list[dict]:
    return [
        {
            "url": reel["url"],
            "folder": reel["folder"],
            "source": reel["source"],
        }
        for reel in load_reels()
    ]


def prune_stale_reels() -> int:
    removed_count = 0

    for reel_meta in JOB_ROOT.glob("*/reel.json"):
        try:
            data = json.loads(reel_meta.read_text(encoding="utf-8"))
        except Exception:
            continue

        reel_url = data.get("reel_url")
        if reel_url and remote_file_exists(reel_url):
            continue

        try:
            reel_meta.unlink(missing_ok=True)
        except TypeError:
            if reel_meta.exists():
                reel_meta.unlink()

        manifest_path = reel_meta.parent / "manifest.json"
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                manifest = None

            if isinstance(manifest, dict):
                manifest["status"] = "deleted"
                manifest.pop("reel", None)
                manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        removed_count += 1

    return removed_count


def start_reel_cleanup_thread(interval_seconds: int = 300) -> None:
    def worker() -> None:
        while True:
            prune_stale_reels()
            time.sleep(interval_seconds)

    threading.Thread(target=worker, daemon=True).start()


def persist_manifest(folder_dir: Path, manifest: dict) -> None:
    (folder_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


@app.route("/")
def home():
    return render_template("index.html", reels=load_reels())


@app.route("/create", methods=["GET", "POST"])
def create():
    myid = uuid.uuid1()
    if request.method == "POST":
        if not imagekit_enabled():
            abort(500, description="IMAGEKIT_PRIVATE_KEY is not configured.")

        rec_id = request.form.get("uuid") or str(myid)
        desc = request.form.get("text", "")
        folder_dir = JOB_ROOT / rec_id
        folder_dir.mkdir(parents=True, exist_ok=True)

        uploaded_files = []
        for file in request.files.values():
            if not file or not file.filename:
                continue

            filename = secure_filename(file.filename)
            if not filename:
                continue

            file_bytes = file.read()
            try:
                upload_result = upload_file_bytes(
                    file_bytes,
                    filename,
                    folder=f"{IMAGEKIT_UPLOAD_FOLDER}/reel-inputs/{rec_id}",
                )
            except Exception as exc:
                abort(500, description=f"ImageKit upload failed for {filename}: {exc}")

            if not upload_result:
                abort(500, description=f"ImageKit upload failed for {filename}.")

            uploaded_files.append(
                {
                    "name": filename,
                    "storage": "imagekit",
                    "url": upload_result["url"],
                    "filePath": upload_result.get("filePath"),
                }
            )

        if not uploaded_files:
            abort(400, description="Please upload at least one file.")

        persist_manifest(
            folder_dir,
            {
                "folder": rec_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "description": desc,
                "files": uploaded_files,
                "status": "queued",
            },
        )

    return render_template("create.html", myid=myid)


@app.route("/gallery")
def gallery():
    return render_template("gallery.html", reels=load_reels())


@app.route("/api/reels")
def api_reels():
    return jsonify({"reels": get_reels_payload()})


if __name__ == "__main__":
    start_generator_process()
    prune_stale_reels()
    start_reel_cleanup_thread()
    app.run(debug=True, use_reloader=False)