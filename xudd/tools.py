import base64
import uuid

from xudd import PY2


def base64_uuid4():
    """
    Return a base64 encoded uuid4
    """
    base64_encoded = base64.urlsafe_b64encode(uuid.uuid4().bytes)
    if not PY2:
        base64_encoded = base64_encoded.decode("utf-8")

    return base64_encoded.rstrip("=")


def is_qualified_id(actor_id):
    """
    See whether or not this actor id is fully qualified (has the
    @hive-id attached) or not.
    """
    return u"@" in actor_id
