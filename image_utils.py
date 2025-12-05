import base64


def encode_image_to_base64(image_path: str) -> str:
    """
    Encode a local image file as base64 string.

    :param image_path: Path to image file (PNG/JPG/JPEG).
    :return: Base64-encoded string.
    """
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
