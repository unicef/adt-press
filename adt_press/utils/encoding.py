import base64


def base64_encode(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")
