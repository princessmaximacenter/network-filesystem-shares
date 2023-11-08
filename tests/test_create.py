import os
import subprocess
from os.path import join as j
from .utils import fabricate_a_source
import pytest


def test_empty_share(shares_dir):
    from nfs4_share.share import Share
    share = Share(shares_dir.join('share'))
    assert os.path.exists(share.directory)


def test_create_with_file(source_dir, shares_dir, calling_prim_group, variables):
    from nfs4_share.manage import create
    items = fabricate_a_source(source_dir, ["file"])
    share = create(shares_dir.join('share'), items=items, managing_groups=[calling_prim_group],
                   domain=variables["domain_name"],
                   service_application_accounts=variables['service_application_accounts'])
    assert os.path.samefile(
        j(share.directory, "file"),
        items[0])


def test_create_with_duplicate_file(source_dir, shares_dir, calling_prim_group, variables):
    from nfs4_share.manage import create
    fabricate_a_source(source_dir, ["file"])
    items = [source_dir.join('file'), source_dir.join('file')]
    share = create(shares_dir.join('share'), items=items, managing_groups=[calling_prim_group],
                   domain=variables["domain_name"],
                   service_application_accounts=variables['service_application_accounts'])
    assert os.path.samefile(
        j(share.directory, "file"),
        items[0])


def test_cli_with_files(source_dir, shares_dir, calling_user, variables):
    items = fabricate_a_source(source_dir, [
        "file1",
        "file2"
    ])
    try:
        subprocess.check_output(['nfs4_share',
                                 '-vv', 'create',
                                 shares_dir.join('share'),
                                 '--domain', variables["domain_name"],
                                 '--item', items[0], items[1],
                                 '-mu', calling_user],
                                stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(e.cmd)
        if e.output is not None:
            print(e.output.decode())
    assert os.path.samefile(shares_dir.join("share", "file1"), items[0])
    assert os.path.samefile(shares_dir.join("share", "file2"), items[1])


def test_create_with_directory(source_dir, shares_dir, calling_prim_group, variables):
    from nfs4_share.manage import create
    fabricate_a_source(source_dir, [
        "dir_with_one_file/file"
    ])
    items = [source_dir.join("dir_with_one_file")]
    share = create(shares_dir.join('share'), items=items, managing_groups=[calling_prim_group],
                   domain=variables["domain_name"],
                   service_application_accounts=variables['service_application_accounts'])
    assert  (j(share.directory, "dir_with_one_file", "file"),
                            j(source_dir, "dir_with_one_file", "file"))


def test_create_with_directory(source_dir, shares_dir, calling_prim_group, variables):
    from nfs4_share.manage import create
    fabricate_a_source(source_dir, [
        "dir_with_one_file/file"
    ])
    items = [source_dir.join("dir_with_one_file"), source_dir.join("dir_with_one_file")]
    share = create(shares_dir.join('share'), items=items, managing_groups=[calling_prim_group],
                   domain=variables["domain_name"],
                   service_application_accounts=variables['service_application_accounts'])
    assert os.path.samefile(j(share.directory, "dir_with_one_file", "file"),
                            j(source_dir, "dir_with_one_file", "file"))


def test_create_with_subsubdirs(source_dir, shares_dir, calling_prim_group, variables):
    from nfs4_share.manage import create
    fabricate_a_source(source_dir, [
        "dir1/dir2/dir3/file",
        "dir1/foo",
        "dir1/bar"
    ])
    items = [source_dir.join("dir1")]
    share = create(shares_dir.join('share'), items=items, managing_groups=[calling_prim_group],
                   domain=variables["domain_name"],
                   service_application_accounts=variables['service_application_accounts'])
    assert os.path.samefile(j(share.directory, "dir1", "dir2", "dir3", "file"),
                            j(source_dir, "dir1", "dir2", "dir3", "file"))


def test_create_with_mixed_items(source_dir, shares_dir, calling_prim_group, variables):
    from nfs4_share.manage import create
    fabricate_a_source(source_dir, [
        "file",
        "dir_with_one_file/file"
    ])
    items = [
        source_dir.join("dir_with_one_file"),
        source_dir.join("file")]
    share = create(shares_dir.join('share'), items=items, managing_groups=[calling_prim_group],
                   domain=variables["domain_name"],
                   service_application_accounts=variables['service_application_accounts'])
    assert os.path.samefile(j(share.directory, "dir_with_one_file", "file"),
                            j(source_dir, "dir_with_one_file", "file"))
    assert os.path.samefile(j(share.directory, "file"),
                            items[1])


def test_create_with_symlinked_file(source_dir, shares_dir, calling_prim_group, variables):
    from nfs4_share.manage import create
    fabricate_a_source(source_dir, [
        "file"
    ])
    os.symlink(os.path.realpath(source_dir.join("file")), source_dir.join("symlink"))
    items = [source_dir.join("symlink")]
    share = create(shares_dir.join('share'), items=items, managing_groups=[calling_prim_group],
                   domain=variables["domain_name"],
                   service_application_accounts=variables['service_application_accounts'])
    assert os.path.samefile(j(share.directory, "symlink"), source_dir.join("file"))


def test_create_with_symlinked_directory(source_dir, shares_dir, calling_prim_group, variables):
    from nfs4_share.manage import create
    fabricate_a_source(source_dir, [
         "dir_with_one_file/file"
    ])
    os.symlink(os.path.realpath(source_dir.join("dir_with_one_file")), source_dir.join("symlink"))
    items = [source_dir.join("symlink")]
    share = create(shares_dir.join('share'), items=items, managing_groups=[calling_prim_group],
                   domain=variables["domain_name"],
                   service_application_accounts=variables['service_application_accounts'])
    assert os.path.samefile(j(share.directory, "symlink", "file"), source_dir.join("dir_with_one_file", "file"))


def test_create_with_relative_symlinked_file(source_dir, shares_dir, calling_prim_group, variables):
    from nfs4_share.manage import create
    fabricate_a_source(source_dir, [
        "file",
        "dir_with_rel_symlink/foo"
    ])
    os.symlink(j("..", "file"), j(source_dir, "dir_with_rel_symlink", "symlink"))
    items = [source_dir.join("dir_with_rel_symlink")]
    share = create(shares_dir.join('share'), items=items, managing_groups=[calling_prim_group],
                   domain=variables["domain_name"],
                   service_application_accounts=variables['service_application_accounts'])
    assert os.path.samefile(j(share.directory, "dir_with_rel_symlink", "symlink"), source_dir.join("file"))


def test_create_with_relative_symlinked_directory(source_dir, shares_dir, calling_prim_group, variables):
    from nfs4_share.manage import create
    fabricate_a_source(source_dir, [
        "dir/file",
        "dir_with_rel_symlink/foo"
    ])
    os.symlink(j("..", "dir"), j(source_dir, "dir_with_rel_symlink", "symlink"))
    items = [j(source_dir, "dir_with_rel_symlink")]
    share = create(shares_dir.join('share'), items=items, managing_groups=[calling_prim_group],
                   domain=variables["domain_name"],
                   service_application_accounts=variables['service_application_accounts'])
    assert os.path.samefile(j(share.directory, "dir_with_rel_symlink", "symlink", "file"),
                            j(source_dir, "dir", "file"))


def test_permissions_create_with_file(source_dir, shares_dir, calling_user, calling_prim_group, variables):
    from nfs4_share import acl
    from nfs4_share.manage import create
    items = fabricate_a_source(source_dir, [
        "file"
    ])
    before_file_permissions = acl.AccessControlList.from_file(items[0])
    users = [calling_user]
    managing_groups = [calling_prim_group]
    pass
    share = create(shares_dir.join('share'), items=items, users=users, managing_groups=managing_groups,
                   domain=variables["domain_name"], lock=False,
                   service_application_accounts=variables['service_application_accounts'])
    user_permissions = acl.AccessControlEntity('A', '', calling_user, variables["domain_name"], 'rxtncy')
    extra_permissions = acl.AccessControlEntity('A', '', variables['service_application_accounts'][0], variables["domain_name"], 'rxtncy')
    managing_group_permissions = acl.AccessControlEntity('A',
                                                         'g',
                                                         calling_prim_group,
                                                         variables["domain_name"],
                                                         'rxwaDdtTNcCo')
    assert user_permissions in share.permissions
    assert extra_permissions in share.permissions
    assert before_file_permissions == acl.AccessControlList.from_file(items[0])
    assert os.path.samefile(j(share.directory, "file"), items[0])

    expected_acl = acl.AccessControlList([user_permissions, extra_permissions, managing_group_permissions])
    share_acl = acl.AccessControlList.from_file(share.directory)
    assert expected_acl == share_acl


def test_htaccess_create_with_file(source_dir, shares_dir, calling_user, calling_prim_group, variables):
    from nfs4_share.manage import create
    items = fabricate_a_source(source_dir, [
        "file"
    ])
    share = create(shares_dir.join('share'), items=items, users=[calling_user], managing_groups=[calling_prim_group],
                   user_apache_directive=variables["user_directive"], group_apache_directive=variables["group_directive"],
                   domain=variables["domain_name"],
                   service_application_accounts=variables['service_application_accounts'])
    expected_htaccess = [
        '<RequireAny>',
        variables["user_directive"].format(calling_user),
        variables["group_directive"].format(calling_prim_group),
        '</RequireAny>'
    ]
    actual_htaccess = []
    with open(os.path.join(share.directory, '.htaccess.files.bioinf'), 'r') as htaccess:
        for entry in htaccess.readlines():
            actual_htaccess.append(entry.rstrip())
    assert expected_htaccess == actual_htaccess


def test_cli_with_missing_file(shares_dir, calling_user):
    proc = subprocess.run(
        ['nfs4_share', 'create', shares_dir.join('share_with_not_existing_file'), '--item',
         "not_existing_file.txt", '-mu',
         calling_user],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with pytest.raises(subprocess.CalledProcessError):
        proc.check_returncode()
    assert not os.path.exists(shares_dir.join('share_with_not_existing_file'))
