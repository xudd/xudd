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
    lotsamessages.main(num_experiments=20, num_steps=20)

### def test_ihc_lotsamessages():
