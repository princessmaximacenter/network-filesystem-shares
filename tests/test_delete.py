import os
import subprocess
import logging
import pytest

from os.path import join as j
from .utils import fabricate_a_source


def test_empty_share_removal(shares_dir, calling_prim_group):
    from nfs4_share.manage import create, delete
    share = create(shares_dir.join('share'), managing_groups=[calling_prim_group],
                   domain="op.umcutrecht.nl")
    assert os.path.exists(share.directory)
    delete(share.directory)
    assert not os.path.exists(share.directory)


def test_file_share_removal(source_dir, shares_dir, calling_prim_group):
    from nfs4_share.manage import create, delete
    items = fabricate_a_source(source_dir, [
        "file"
    ])
    share = create(shares_dir.join('share'), items=items, managing_groups=[calling_prim_group],
                   domain="op.umcutrecht.nl")
    assert os.path.exists(j(share.directory, "file"))
    delete(share.directory)
    assert not os.path.exists(j(share.directory, "file"))


def test_dir_share_removal(source_dir, shares_dir, calling_prim_group):
    from nfs4_share.manage import create, delete
    fabricate_a_source(source_dir, [
        "dir/file"
    ])
    items = [source_dir.join('dir')]
    share = create(shares_dir.join('share'), items=items, managing_groups=[calling_prim_group],
                   domain="op.umcutrecht.nl")
    assert os.path.exists(j(share.directory, "dir"))
    delete(share.directory)
    assert not os.path.exists(j(share.directory, "dir"))


def test_cli_removal(source_dir, shares_dir, calling_prim_group):
    from nfs4_share.manage import create
    items = fabricate_a_source(source_dir, ["file"])
    share = create(shares_dir.join('share'), items=items, managing_groups=[calling_prim_group],
                   domain="op.umcutrecht.nl")
    assert os.path.exists(j(share.directory, "file"))
    try:
        subprocess.check_output(['nfs4_share', 'delete', share.directory])
    except subprocess.CalledProcessError as e:
        print(e.cmd)
        if e.stdout is not None:
            print(e.stdout.decode())
        if e.stderr is not None:
            print(e.stderr.decode())
    assert not os.path.exists(shares_dir.join("share").join("file"))


def test_multiple_shares_on_single_file_with_removal(source_dir, shares_dir, calling_prim_group):
    from nfs4_share.manage import create, delete
    import nfs4_share.acl as nfs4_acl
    items = fabricate_a_source(source_dir, [
        "file"
    ])

    share1 = create(shares_dir.join('share1'), items=items, managing_groups=[calling_prim_group],
                    domain="op.umcutrecht.nl", lock=False)
    share1_nfs4_acl = nfs4_acl.AccessControlList.from_file(items[0])
    share2 = create(shares_dir.join('share2'), items=items, managing_groups=[calling_prim_group],
                    domain="op.umcutrecht.nl", lock=False)
    share1_2_nfs4_acl = nfs4_acl.AccessControlList.from_file(items[0])
    share3 = create(shares_dir.join('share3'), items=items, managing_groups=[calling_prim_group],
                    domain="op.umcutrecht.nl", lock=False)
    share1_2_3_nfs4_acl = nfs4_acl.AccessControlList.from_file(items[0])
    try:
        delete(share3.directory)
        share1_2_3_min_3_acl = nfs4_acl.AccessControlList.from_file(items[0])
        assert share1_2_nfs4_acl == share1_2_3_min_3_acl
    except AssertionError as e:
        print("share1_2_nfs4_acl:\t%s" % share1_2_nfs4_acl)
        print("share1_2_3_nfs4_acl\t%s" % share1_2_3_nfs4_acl)
        print("share1_2_3_min_3_acl:\t%s" % share1_2_3_min_3_acl)
        raise e
    try:
        delete(share2.directory)
        share1_2_3_min_3_2_acl = nfs4_acl.AccessControlList.from_file(items[0])
        assert share1_nfs4_acl == share1_2_3_min_3_2_acl
    except AssertionError as e:
        print("share1_nfs4_acl:\t%s" % share1_nfs4_acl)
        print("share1_2_3_min_3_2_acl:\t%s" % share1_2_3_min_3_2_acl)
        raise e


def test_removal_of_file_permission(source_dir, shares_dir, calling_user, calling_prim_group):
    from nfs4_share.manage import create, delete
    import nfs4_share.acl as nfs4_acl
    items = fabricate_a_source(source_dir, [
        "file"
    ])
    before_nfs4_acl = nfs4_acl.AccessControlList.from_file(items[0])
    share = create(shares_dir.join('share'), items=items, users=[calling_user],
                   managing_groups=[calling_prim_group],
                   domain="op.umcutrecht.nl")

    with_nfs4_acl = nfs4_acl.AccessControlList.from_file(items[0])
    delete(share.directory)
    after_nfs4_acl = nfs4_acl.AccessControlList.from_file(items[0])
    try:
        assert before_nfs4_acl == after_nfs4_acl
    except AssertionError as e:
        print("before:\t%s" % before_nfs4_acl)
        print("with:\t%s" % with_nfs4_acl)
        print("after:\t%s" % after_nfs4_acl)
        raise e


def test_prevention_perm_removal_of_file(source_dir, shares_dir, calling_user, calling_prim_group):
    from nfs4_share.manage import create, delete
    items = fabricate_a_source(source_dir, [
        "file"
    ])
    share = create(shares_dir.join('share'), items=items, users=[calling_user],
                   managing_groups=[calling_prim_group],
                   domain="op.umcutrecht.nl")

    os.remove(items[0])  # Remove original file
    assert not os.path.exists(items[0])  # Ensure it is gone

    # Try deleting the share without a force
    logging.disable(logging.ERROR)  # to hide the ERROR being logged on the next level

    with pytest.raises(FileNotFoundError):
        delete(share.directory)

    logging.disable(logging.NOTSET)  # re-enable full logging

    # Make sure the file is still in the share
    assert os.path.exists(j(share.directory, 'file'))

    # Retry with force applied
    delete(share.directory, force=True)

    assert not os.path.exists(j(share.directory, 'file'))


def test_removing_file_instead_of_share(source_dir, shares_dir, calling_user, calling_prim_group):
    from nfs4_share.manage import create, delete
    items = fabricate_a_source(source_dir, [
        "file"
    ])
    share = create(shares_dir.join('share'), items=items, users=[calling_user],
                   managing_groups=[calling_prim_group],
                   domain="op.umcutrecht.nl")

    from nfs4_share.share import IllegalShareSetupError
    with pytest.raises(IllegalShareSetupError):
        delete(j(share.directory, 'file'))

    assert os.path.exists(j(share.directory, 'file'))
