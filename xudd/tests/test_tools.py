from xudd import tools

import mock

class FakeUUID(object):
    bytes = b'\x05\x8f8\x83\x93mI`\xab\xa1\x96N\xbb\x1fE\x84'

UUID_MOCK = mock.Mock(return_value=FakeUUID())


@mock.patch('uuid.uuid4', UUID_MOCK)
def test_base64_unicode():
    assert tools.base64_uuid4() == u"BY84g5NtSWCroZZOux9FhA"


def test_is_qualified_id():
    assert tools.is_qualified_id("foo@bar") is True
    assert tools.is_qualified_id("foo") is False


def test_split_id():
    assert tools.split_id("actor@hive") == ["actor", "hive"]
    assert tools.split_id("actor") == ["actor", None]

    # We really shouldn't have any formatted like this, but just
    # in case...
    assert tools.split_id("actor@hive@garbage") == ["actor", "hive@garbage"]
