import base64
import uuid

from xudd import PY2


def base64_uuid():
    """
    Return a base64 encoded uuid4
    """
    base64_encoded = base64.urlsafe_b64encode(uuid.uuid4().bytes)
    if not PY2:
        base64_encoded = base64_encoded.decode("utf-8")

    return base64_encoded.rstrip("=")
