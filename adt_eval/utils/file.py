import base64
import json
from pathlib import Path

def encode_image_to_base64(image_path: str | Path | None) -> str | None:
    if not image_path:
        return None
    try:
        path = Path(image_path)
        with path.open("rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return None

def save_json(path: str | Path, data) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=True, indent=2)

def load_json(path: str | Path):
    file_path = Path(path)
    with file_path.open("r", encoding="utf8") as f:
        return json.load(f)
