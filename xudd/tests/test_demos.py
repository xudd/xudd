from xudd.demos import special_hive
from xudd.demos import lotsamessages

def test_special_hive():
    """
    This demo tests that demos are actually actors and are in fact subclassable.
    """
    special_hive.main()


def test_lotsamessages():
    """
    Test the lotsamessages demo (but not with too many messages ;))
    """
    assert lotsamessages.main(num_experiments=20, num_steps=20) is True


## Commenting out for now due to Travis issue:
##   https://github.com/travis-ci/travis-cookbooks/issues/155
## easier than researching a workaround ;p
#
# def test_lotsamessages_ihc():
#     """
#     Test the lotsamessages demo with inter-hive communication
#     """
#     assert lotsamessages.main(
#         num_experiments=20, num_steps=20, subprocesses=4) is True
