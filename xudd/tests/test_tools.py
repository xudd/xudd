from xudd import tools

import mock

class FakeUUID(object):
    bytes = b'\x05\x8f8\x83\x93mI`\xab\xa1\x96N\xbb\x1fE\x84'

UUID_MOCK = mock.Mock(return_value=FakeUUID())


@mock.patch('uuid.uuid4', UUID_MOCK)
def test_base64_unicode():
    assert tools.base64_uuid() == u"BY84g5NtSWCroZZOux9FhA"
