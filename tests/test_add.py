from .utils import fabricate_a_source
import pytest
import os
import subprocess


@pytest.fixture(scope='function')
def single_file_share(source_dir, shares_dir, calling_user, calling_prim_group, variables):
    from nfs4_share.manage import create
    items = fabricate_a_source(source_dir, [
        "file"
    ])
    user_directive = "Require ldap-user {}"
    group_directive = "Require ldap-group cn={},cn=users,dc=genomics,dc=op,dc=umcutrecht,dc=nl"
    share = create(shares_dir.join('share'), items=items, users=[calling_user], managing_groups=[calling_prim_group],
                   user_apache_directive=user_directive, group_apache_directive=group_directive,
                   domain="op.umcutrecht.nl",
                   service_application_accounts=variables['service_application_accounts'])
    return share


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


def test_add_user(single_file_share, extra_user="hkerstens"):
    from nfs4_share.manage import add
    from nfs4_share import acl
    extra_user_permissions = acl.AccessControlEntity('A', '', extra_user, 'op.umcutrecht.nl', 'rxtncy')
    before_share_permissions = acl.AccessControlList.from_file(single_file_share.directory)

    add(single_file_share.directory, users=[extra_user], domain='op.umcutrecht.nl', lock=True)
    after_share_permissions = acl.AccessControlList.from_file(single_file_share.directory)

    assert after_share_permissions == before_share_permissions + acl.AccessControlList([extra_user_permissions])


def test_add_group(single_file_share, extra_group="pmc_research"):
    from nfs4_share.manage import add
    from nfs4_share import acl
    extra_user_permissions = acl.AccessControlEntity('A', 'g', extra_group, 'op.umcutrecht.nl', 'rxtncy')
    before_share_permissions = acl.AccessControlList.from_file(single_file_share.directory)

    add(single_file_share.directory, groups=[extra_group], domain='op.umcutrecht.nl', lock=True)
    after_share_permissions = acl.AccessControlList.from_file(single_file_share.directory)

    assert after_share_permissions == before_share_permissions + acl.AccessControlList([extra_user_permissions])


def test_cli_with_file(single_file_share, source_dir, variables):
    items = fabricate_a_source(source_dir, [
        "extra_file"
    ])
    try:
        subprocess.check_output(['nfs4_share',
                                 '-vv', 'add',
                                 single_file_share.directory,
                                 '--item', items[0]],
                                stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(e.cmd)
        if e.output is not None:
            print(e.output.decode())
    assert os.path.samefile(os.path.join(single_file_share.directory, "extra_file"), items[0])
