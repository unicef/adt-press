import base64
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