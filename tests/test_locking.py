import os
from os.path import join as j
from .utils import fabricate_a_source
import pytest


def test_lock_on_single_file(calling_prim_group, source_dir, shares_dir):
    from nfs4_share.manage import create, delete

    items = fabricate_a_source(source_dir, ["file"])
    share_dir = shares_dir.join("share")
    share = create(share_dir,
                   items=items,
                   managing_groups=[calling_prim_group],
                   domain="op.umcutrecht.nl",
                   lock=True)

    # Try deleting it manually, should fail
    with pytest.raises(PermissionError):
        os.remove(share_dir.join("file"))
    assert os.path.exists(j(share.directory, "file"))

    # Try deleting it via the share_dir stuff
    delete(share_dir)
    assert not os.path.exists(j(share.directory, "file"))
