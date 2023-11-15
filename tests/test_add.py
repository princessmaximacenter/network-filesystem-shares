from .utils import fabricate_a_source
import pytest
import os
import subprocess

def test_null_add_share(single_file_share):
    from nfs4_share.manage import add
    add(single_file_share.directory)
    assert os.path.isdir(single_file_share.directory)


def test_add_file(single_file_share, source_dir):
    from nfs4_share.manage import add
    items = fabricate_a_source(source_dir, [
        "extra_file"
    ])

    add(single_file_share.directory, items=items)
    expected_file_added = os.path.join(single_file_share.directory, os.path.basename(items[0]))
    expected_file_original = os.path.join(single_file_share.directory, "file")
    assert os.path.exists(expected_file_added)
    assert os.path.exists(expected_file_original)
    assert os.path.samefile(expected_file_added, items[0])


def test_add_user(single_file_share, variables):
    from nfs4_share.manage import add
    from nfs4_share import acl
    extra_user_permissions = acl.AccessControlEntity('A', '', variables["account_someone_else"],
                                                     variables["domain_name"], 'rxtncy')
    before_share_permissions = acl.AccessControlList.from_file(single_file_share.directory)

    add(single_file_share.directory, users=[variables["account_someone_else"]], domain=variables["domain_name"],
        lock=True, user_apache_directive=variables["user_directive"],
        group_apache_directive=variables["group_directive"])
    after_share_permissions = acl.AccessControlList.from_file(single_file_share.directory)

    assert sorted(after_share_permissions.entries) == sorted(before_share_permissions.entries +
                                                             acl.AccessControlList([extra_user_permissions]).entries)


def test_add_group(single_file_share, variables, extra_group="pmc_research"):
    from nfs4_share.manage import add
    from nfs4_share import acl
    extra_user_permissions = acl.AccessControlEntity('A', 'g', extra_group, variables["domain_name"], 'rxtncy')
    before_share_permissions = acl.AccessControlList.from_file(single_file_share.directory)

    add(single_file_share.directory, groups=[extra_group], domain=variables["domain_name"], lock=True,
        user_apache_directive=variables["user_directive"], group_apache_directive=variables["group_directive"])
    after_share_permissions = acl.AccessControlList.from_file(single_file_share.directory)

    assert sorted(after_share_permissions.entries) == sorted(before_share_permissions.entries +
                                                             acl.AccessControlList([extra_user_permissions]).entries)


def test_cli_with_file(single_file_share, source_dir, variables):
    items = fabricate_a_source(source_dir, [
        "extra_file"
    ])
    try:
        subprocess.check_output(['nfs4_share',
                                 '-vv', 'add',
                                 single_file_share.directory,
                                 '--domain', variables["domain_name"],
                                 '--item', items[0]],
                                stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(e.cmd)
        if e.output is not None:
            print(e.output.decode())
    assert os.path.samefile(os.path.join(single_file_share.directory, "extra_file"), items[0])
