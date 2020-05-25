import os
import subprocess
from os.path import join as j

from tests.base_test import TestBase


class TestCreate(TestBase):

    def test_empty_share(self):
        from nfs4_share.share import Share
        share = Share(os.path.join(self.working_dir, 'share'))
        self.assertTrue(os.path.exists(share.directory))

    def test_create_with_file(self):
        from nfs4_share.manage import create
        source = self.fabricate([
            "file"
        ])
        items = [j(source, 'file')]
        share = create(j(self.working_dir, 'share'), items=items, managing_groups=[self.calling_prim_group],
                       domain="op.umcutrecht.nl")
        self.assertTrue(os.path.samefile(
            j(share.directory, "file"),
            items[0]))

    def test_create_with_duplicate_file(self):
        from nfs4_share.manage import create
        source = self.fabricate([
            "file"
        ])
        items = [j(source, 'file'),j(source, 'file')]
        share = create(j(self.working_dir, 'share'), items=items, managing_groups=[self.calling_prim_group],
                       domain="op.umcutrecht.nl")
        self.assertTrue(os.path.samefile(
            j(share.directory, "file"),
            items[0]))

    def test_cli_with_files(self):
        source = self.fabricate([
            "file1",
            "file2"
        ])
        items = [j(source, 'file1'), j(source, 'file2')]
        try:
            subprocess.check_output(['nfs4_share',
                                    '-vv', 'create', 
                                    j(self.working_dir, 'share'), 
                                    '--item', items[0], items[1], 
                                    '-mu', self.calling_user],
                                    stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print(e.cmd)
            if e.output is not None:
                print(e.output.decode())
        self.assertTrue(os.path.samefile(
            j(self.working_dir, 'share', "file1"),
            items[0]))
        self.assertTrue(os.path.samefile(
            j(self.working_dir, 'share', "file2"),
            items[1]))

    def test_create_with_directory(self):
        from nfs4_share.manage import create
        source = self.fabricate([
            "dir_with_one_file/file"
        ])
        items = [j(source, "dir_with_one_file")]
        share = create(os.path.join(self.working_dir, 'share'), items=items, managing_groups=[self.calling_prim_group],
                       domain="op.umcutrecht.nl")
        self.assertTrue(os.path.samefile(
            j(share.directory, "dir_with_one_file", "file"),
            j(source, "dir_with_one_file", "file")))

    def test_create_with_duplicate_directory(self):
        from nfs4_share.manage import create
        source = self.fabricate([
            "dir_with_one_file/file"
        ])
        items = [j(source, "dir_with_one_file"), j(source, "dir_with_one_file")]
        share = create(os.path.join(self.working_dir, 'share'), items=items, managing_groups=[self.calling_prim_group],
                       domain="op.umcutrecht.nl")
        self.assertTrue(os.path.samefile(
            j(share.directory, "dir_with_one_file", "file"),
            j(source, "dir_with_one_file", "file")))

    def test_create_with_subsubdirs(self):
        from nfs4_share.manage import create
        source = self.fabricate([
            "dir1/dir2/dir3/file",
            "dir1/foo",
            "dir1/bar"
        ])
        items = [j(source, "dir1")]
        share = create(os.path.join(self.working_dir, 'share'), items=items, managing_groups=[self.calling_prim_group],
                       domain="op.umcutrecht.nl")
        self.assertTrue(os.path.samefile(
            j(share.directory, "dir1", "dir2", "dir3", "file"),
            j(source, "dir1", "dir2", "dir3", "file")))

    def test_create_with_mixed_items(self):
        from nfs4_share.manage import create
        source = self.fabricate([
            "file",
            "dir_with_one_file/file"
        ])
        items = [
            j(source, "dir_with_one_file"),
            j(source, "file")]
        share = create(os.path.join(self.working_dir, 'share'), items=items, managing_groups=[self.calling_prim_group],
                       domain="op.umcutrecht.nl")
        self.assertTrue(os.path.samefile(
            j(share.directory, "dir_with_one_file", "file"),
            j(source, "dir_with_one_file", "file")))
        self.assertTrue(os.path.samefile(
            j(share.directory, "file"),
            items[1]))

    def test_create_with_symlinked_file(self):
        from nfs4_share.manage import create
        source = self.fabricate([
            "file"
        ])
        os.symlink(j(os.path.realpath(source), "file"), j(source, "symlink"))
        items = [j(source, 'symlink')]
        share = create(j(self.working_dir, 'share'), items=items, managing_groups=[self.calling_prim_group],
                       domain="op.umcutrecht.nl")
        self.assertTrue(os.path.samefile(
            j(share.directory, "symlink"),
            j(source, "file")))

    def test_create_with_symlinked_directory(self):
        from nfs4_share.manage import create
        source = self.fabricate([
            "dir_with_one_file/file"
        ])
        os.symlink(j(os.path.realpath(source), "dir_with_one_file"), j(source, "symlink"))
        items = [j(source, "symlink")]
        share = create(os.path.join(self.working_dir, 'share'), items=items, managing_groups=[self.calling_prim_group],
                       domain="op.umcutrecht.nl")
        self.assertTrue(os.path.samefile(
            j(share.directory, "symlink", "file"),
            j(source, "dir_with_one_file", "file")))

    def test_create_with_relative_symlinked_file(self):
        from nfs4_share.manage import create
        source = self.fabricate([
            "file",
            "dir_with_rel_symlink/foo"
        ])
        os.symlink(j("..", "file"), j(source, "dir_with_rel_symlink", "symlink"))
        items = [j(source, "dir_with_rel_symlink")]
        share = create(os.path.join(self.working_dir, 'share'), items=items, managing_groups=[self.calling_prim_group],
                       domain="op.umcutrecht.nl")
        self.assertTrue(os.path.samefile(
            j(share.directory, "dir_with_rel_symlink", "symlink"),
            j(source, "file")))

    def test_create_with_relative_symlinked_directory(self):
        from nfs4_share.manage import create
        source = self.fabricate([
            "dir/file",
            "dir_with_rel_symlink/foo"
        ])
        os.symlink(j("..", "dir"), j(source, "dir_with_rel_symlink", "symlink"))
        items = [j(source, "dir_with_rel_symlink")]
        share = create(os.path.join(self.working_dir, 'share'), items=items, managing_groups=[self.calling_prim_group],
                       domain="op.umcutrecht.nl")
        self.assertTrue(os.path.samefile(
            j(share.directory, "dir_with_rel_symlink", "symlink", "file"),
            j(source, "dir", "file")))

    def test_permissions_create_with_file(self):
        from nfs4_share import acl
        from nfs4_share.manage import create
        source = self.fabricate([
            "file"
        ])
        items = [j(source, 'file')]
        users = [self.calling_user]
        managing_groups = [self.calling_prim_group]
        share = create(j(self.working_dir, 'share'), items=items, users=users, managing_groups=managing_groups,
                       domain="op.umcutrecht.nl", lock=False)
        user_permissions = acl.AccessControlEntity('A', '', self.calling_user, 'op.umcutrecht.nl', 'rxtncy')
        extra_permissions = acl.AccessControlEntity('A', '', 'gen_apache', 'op.umcutrecht.nl', 'rxtncy')
        managing_group_permissions = acl.AccessControlEntity('A',
                                                             'g',
                                                             self.calling_prim_group,
                                                             'op.umcutrecht.nl',
                                                             'rxwadtTNcCo')
        self.assertTrue(user_permissions in share.permissions)
        self.assertTrue(extra_permissions in share.permissions)
        self.assertTrue(os.path.samefile(
            j(share.directory, "file"),
            items[0]))
        expected_acl = acl.AccessControlList([user_permissions, extra_permissions, managing_group_permissions])
        file_acl = acl.AccessControlList.from_file(j(share.directory, "file"))
        share_acl = acl.AccessControlList.from_file(share.directory)
        self.assertEqual(expected_acl, share_acl)
        self.assertTrue(user_permissions in file_acl)

    def test_htaccess_create_with_file(self):
        from nfs4_share.manage import create
        source = self.fabricate([
            "file"
        ])
        items = [j(source, 'file')]
        users = [self.calling_user]
        managing_groups = [self.calling_prim_group]
        user_directive = "Require ldap-user {}"
        group_directive = "Require ldap-group cn={},cn=users,dc=genomics,dc=op,dc=umcutrecht,dc=nl"
        share = create(j(self.working_dir, 'share'), items=items, users=users, managing_groups=managing_groups,
                       user_apache_directive=user_directive, group_apache_directive=group_directive,
                       domain="op.umcutrecht.nl")
        expected_htaccess = [
            '<RequireAny>',
            user_directive.format(self.calling_user),
            group_directive.format(self.calling_prim_group),
            '</RequireAny>'
        ]
        actual_htaccess = []
        with open(os.path.join(share.directory, '.htaccess.files.bioinf'), 'r') as htaccess:
            for entry in htaccess.readlines():
                actual_htaccess.append(entry.rstrip())
        self.assertEqual(expected_htaccess, actual_htaccess)

    def test_cli_with_missing_file(self):
        proc = subprocess.run(
                ['python3', '-m', 'nfs4_share', 'create', j(self.working_dir, 'share_with_not_existing_file'), '--item', "not_existing_file.txt", '-mu',
                 self.calling_user],
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with self.assertRaises(subprocess.CalledProcessError):
            proc.check_returncode()
        self.assertTrue(not os.path.exists(j(self.working_dir, 'share_with_not_existing_file')))
