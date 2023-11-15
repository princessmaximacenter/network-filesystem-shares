import os
import subprocess
import logging
import pytest

from os.path import join as j
from .utils import fabricate_a_source

def test_empty_share_removal(shares_dir, calling_prim_group, variables):
    from nfs4_share.manage import create, delete
    share = create(shares_dir.join('share'), managing_groups=[calling_prim_group],
                   domain=variables["domain_name"])
    assert os.path.exists(share.directory)
    delete(share.directory)
    assert not os.path.exists(share.directory)


def test_file_share_removal(source_dir, shares_dir, calling_prim_group, variables):
    from nfs4_share.manage import create, delete
    items = fabricate_a_source(source_dir, [
        "file"
    ])
    share = create(shares_dir.join('share'), items=items, managing_groups=[calling_prim_group],
                   domain=variables["domain_name"])
    assert os.path.exists(j(share.directory, "file"))
    delete(share.directory)
    assert not os.path.exists(j(share.directory, "file"))


def test_dir_share_removal(source_dir, shares_dir, calling_prim_group, variables):
    from nfs4_share.manage import create, delete
    fabricate_a_source(source_dir, [
        "dir/file"
    ])
    items = [source_dir.join('dir')]
    share = create(shares_dir.join('share'), items=items, managing_groups=[calling_prim_group],
                   domain=variables["domain_name"])
    assert os.path.exists(j(share.directory, "dir"))
    delete(share.directory)
    assert not os.path.exists(j(share.directory, "dir"))


def test_cli_removal(source_dir, shares_dir, calling_prim_group, variables):
    from nfs4_share.manage import create
    items = fabricate_a_source(source_dir, ["file"])
    share = create(shares_dir.join('share'), items=items, managing_groups=[calling_prim_group],
                   domain=variables["domain_name"])
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


def test_multiple_shares_on_single_file_with_removal(source_dir, shares_dir, calling_prim_group, variables):
    from nfs4_share.manage import create, delete
    import nfs4_share.acl as nfs4_acl
    items = fabricate_a_source(source_dir, [
        "file"
    ])

    share1 = create(shares_dir.join('share1'), items=items, managing_groups=[calling_prim_group],
                    domain=variables["domain_name"], lock=False)
    share1_nfs4_acl = nfs4_acl.AccessControlList.from_file(items[0])
    share2 = create(shares_dir.join('share2'), items=items, managing_groups=[calling_prim_group],
                    domain=variables["domain_name"], lock=False)
    share1_2_nfs4_acl = nfs4_acl.AccessControlList.from_file(items[0])
    share3 = create(shares_dir.join('share3'), items=items, managing_groups=[calling_prim_group],
                    domain=variables["domain_name"], lock=False)
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


def test_removal_of_file_permission(source_dir, shares_dir, calling_user, calling_prim_group, variables):
    from nfs4_share.manage import create, delete
    import nfs4_share.acl as nfs4_acl
    items = fabricate_a_source(source_dir, [
        "file"
    ])
    before_nfs4_acl = nfs4_acl.AccessControlList.from_file(items[0])
    share = create(shares_dir.join('share'), items=items, users=[calling_user],
                   managing_groups=[calling_prim_group],
                   domain=variables["domain_name"])

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


def test_prevention_perm_removal_of_file(source_dir, shares_dir, calling_user, calling_prim_group, variables):
    from nfs4_share.manage import create, delete
    items = fabricate_a_source(source_dir, [
        "file"
    ])
    share = create(shares_dir.join('share'), items=items, users=[calling_user],
                   managing_groups=[calling_prim_group],
                   domain=variables["domain_name"])

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


def test_removing_file_instead_of_share(source_dir, shares_dir, calling_user, calling_prim_group, variables):
    from nfs4_share.manage import create, delete
    items = fabricate_a_source(source_dir, [
        "file"
    ])
    share = create(shares_dir.join('share'), items=items, users=[calling_user],
                   managing_groups=[calling_prim_group],
                   domain=variables["domain_name"])

    from nfs4_share.share import IllegalShareSetupError
    with pytest.raises(IllegalShareSetupError):
        delete(j(share.directory, 'file'))

    assert os.path.exists(j(share.directory, 'file'))

def test_remove_one_user(single_file_share, variables):
    from nfs4_share.manage import add,delete, generate_permissions
    from nfs4_share import acl

    # add multiple users to the test share
    extra_user_permissions = generate_permissions(users=variables["multiple_new_users"], 
                                                  groups=[], managing_users=[], managing_groups=[], 
                                                  domain=variables["domain_name"], manage_permissions='rxtncy')
    before_share_permissions = acl.AccessControlList.from_file(single_file_share.directory)
    expected_acl_after_add = before_share_permissions + extra_user_permissions

    add(single_file_share.directory, users=variables["multiple_new_users"], domain=variables["domain_name"],
        lock=True, user_apache_directive=variables["user_directive"],
        group_apache_directive=variables["group_directive"])
    after_share_permissions = acl.AccessControlList.from_file(single_file_share.directory)

    assert sorted(after_share_permissions.entries) == sorted(expected_acl_after_add.entries)
    
    acl_tobe_removed = acl.AccessControlEntity('A', '', 
                                               variables["user_to_rm_from_share"],
                                               variables["domain_name"], 'rxtncy')
    acl_expected_after_rm = after_share_permissions - acl.AccessControlList([acl_tobe_removed])

    delete(single_file_share.directory, domain=variables["domain_name"], users=[variables["user_to_rm_from_share"]], lock=True)
    acl_after_user_rm = acl.AccessControlList.from_file(single_file_share.directory)
    assert sorted(acl_after_user_rm.entries) == sorted(acl_expected_after_rm.entries)

def test_remove_multiple_users(single_file_share, variables):
    from nfs4_share.manage import add,delete, generate_permissions
    from nfs4_share import acl

    # add multiple users to the test share
    extra_user_permissions = generate_permissions(users=variables["multiple_new_users"], 
                                                  groups=[], managing_users=[], managing_groups=[], 
                                                  domain=variables["domain_name"], manage_permissions='rxtncy')
    before_share_permissions = acl.AccessControlList.from_file(single_file_share.directory)
    expected_acl_after_add = before_share_permissions + extra_user_permissions

    add(single_file_share.directory, users=variables["multiple_new_users"], domain=variables["domain_name"],
        lock=True, user_apache_directive=variables["user_directive"],
        group_apache_directive=variables["group_directive"])
    after_share_permissions = acl.AccessControlList.from_file(single_file_share.directory)

    assert sorted(after_share_permissions.entries) == sorted(expected_acl_after_add.entries)
    
    acl_expected_after_rm = acl.AccessControlList(set(after_share_permissions) - set(extra_user_permissions))

    delete(single_file_share.directory, domain=variables["domain_name"], users=variables["multiple_new_users"], lock=True)
    acl_after_user_rm = acl.AccessControlList.from_file(single_file_share.directory)
    assert sorted(acl_after_user_rm.entries) == sorted(acl_expected_after_rm.entries)

def test_remove_one_item(source_dir, shares_dir, calling_prim_group, variables):
    from nfs4_share.manage import create,delete
    items = fabricate_a_source(source_dir, ["file","file1","file2"])
    share = create(shares_dir.join('share'), items=items, managing_groups=[calling_prim_group],
                   domain=variables["domain_name"],
                   service_application_accounts=variables['service_application_accounts'])
    
    expected_items_after_deletion = os.listdir(share.directory)
    expected_items_after_deletion.remove('file')
    delete(share.directory, items=["file"])
    items_after_deletion = os.listdir(share.directory)
    assert sorted(items_after_deletion) == sorted(expected_items_after_deletion)

def test_remove_multiple_items(source_dir, shares_dir, calling_prim_group, variables):
    from nfs4_share.manage import create,delete
    items = fabricate_a_source(source_dir, ["file","file1","file2"])
    share = create(shares_dir.join('share'), items=items, managing_groups=[calling_prim_group],
                   domain=variables["domain_name"],
                   service_application_accounts=variables['service_application_accounts'])
    
    expected_items_after_deletion = list(set(os.listdir(share.directory)) - set(['file', 'file1']))
    delete(share.directory, items=["file", "file1"])
    items_after_deletion = os.listdir(share.directory)
    assert sorted(items_after_deletion) == sorted(expected_items_after_deletion)