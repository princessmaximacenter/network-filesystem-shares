from tests.base_test import TestBase

import os
import subprocess
import logging

from os.path import join as j


class TestRemove(TestBase):

    def test_empty_share_removal(self):
        from nfs4_share.manage import create, delete
        share = create(j(self.working_dir, 'share'), managing_groups=[self.calling_prim_group],
                       domain="op.umcutrecht.nl")
        self.assertTrue(os.path.exists(share.directory))
        delete(share.directory)
        self.assertFalse(os.path.exists(share.directory))

    def test_file_share_removal(self):
        from nfs4_share.manage import create, delete
        source = self.fabricate([
            "file"
        ])
        items = [j(source, 'file')]
        share = create(j(self.working_dir, 'share'), items=items, managing_groups=[self.calling_prim_group],
                       domain="op.umcutrecht.nl")
        self.assertTrue(os.path.exists(
            j(share.directory, "file")))
        delete(share.directory)
        self.assertFalse(os.path.exists(
            j(share.directory, "file")))

    def test_dir_share_removal(self):
        from nfs4_share.manage import create, delete
        source = self.fabricate([
            "dir/file"
        ])
        items = [j(source, 'dir')]
        share = create(j(self.working_dir, 'share'), items=items, managing_groups=[self.calling_prim_group],
                       domain="op.umcutrecht.nl")
        self.assertTrue(os.path.exists(
            j(share.directory, "dir")))
        delete(share.directory)
        self.assertFalse(os.path.exists(
            j(share.directory, "dir")))

    def test_cli_removal(self):
        from nfs4_share.manage import create
        source = self.fabricate([
            "file"
        ])
        items = [j(source, 'file')]
        share = create(j(self.working_dir, 'share'), items=items, managing_groups=[self.calling_prim_group],
                       domain="op.umcutrecht.nl")
        self.assertTrue(os.path.exists(
            j(share.directory, "file")))
        try:
            subprocess.check_call(['nfs4_share', 'delete', j(self.working_dir, 'share')],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            print(e.cmd)
            if e.stdout is not None:
                print(e.stdout.decode())
            if e.stderr is not None:
                print(e.stderr.decode())
        self.assertFalse(os.path.exists(
            j(share.directory, "file")))

    def test_multiple_shares_on_single_file_with_removal(self):
        from nfs4_share.manage import create, delete
        import nfs4_share.acl as nfs4_acl
        source = self.fabricate([
            "file"
        ])
        items = [j(source, 'file')]

        share1 = create(j(self.working_dir, 'share1'), items=items, users=[self.calling_user],
                        managing_groups=[self.calling_prim_group],
                        domain="op.umcutrecht.nl", lock=False)
        share1_nfs4_acl = nfs4_acl.AccessControlList.from_file(items[0])
        share2 = create(j(self.working_dir, 'share2'), items=items, users=[self.calling_user],
                        managing_groups=[self.calling_prim_group],
                        domain="op.umcutrecht.nl", lock=False)
        share1_2_nfs4_acl = nfs4_acl.AccessControlList.from_file(items[0])
        share3 = create(j(self.working_dir, 'share3'), items=items, users=[self.calling_user],
                        managing_groups=[self.calling_prim_group],
                        domain="op.umcutrecht.nl", lock=False)
        share1_2_3_nfs4_acl = nfs4_acl.AccessControlList.from_file(items[0])
        try:
            delete(share3.directory)
            share1_2_3_min_3_acl = nfs4_acl.AccessControlList.from_file(items[0])
            self.assertEqual(share1_2_nfs4_acl, share1_2_3_min_3_acl)
        except AssertionError as e:
            print("share1_2_nfs4_acl:\t%s" % share1_2_nfs4_acl)
            print("share1_2_3_nfs4_acl\t%s" % share1_2_3_nfs4_acl)
            print("share1_2_3_min_3_acl:\t%s" % share1_2_3_min_3_acl)
            raise e
        try:
            delete(share2.directory)
            share1_2_3_min_3_2_acl = nfs4_acl.AccessControlList.from_file(items[0])
            self.assertEqual(share1_nfs4_acl, share1_2_3_min_3_2_acl)
        except AssertionError as e:
            print("share1_nfs4_acl:\t%s" % share1_nfs4_acl)
            print("share1_2_3_min_3_2_acl:\t%s" % share1_2_3_min_3_2_acl)
            raise e

    def test_file_permission_removal(self):
        from nfs4_share.manage import create, delete
        import nfs4_share.acl as nfs4_acl
        source = self.fabricate([
            "file"
        ])
        items = [j(source, 'file')]
        before_nfs4_acl = nfs4_acl.AccessControlList.from_file(items[0])
        share = create(j(self.working_dir, 'share'), items=items, users=[self.calling_user],
                       managing_groups=[self.calling_prim_group],
                       domain="op.umcutrecht.nl")

        with_nfs4_acl = nfs4_acl.AccessControlList.from_file(items[0])
        delete(share.directory)
        after_nfs4_acl = nfs4_acl.AccessControlList.from_file(items[0])
        try:
            self.assertEqual(before_nfs4_acl, after_nfs4_acl)
        except AssertionError as e:
            print("before:\t%s" % before_nfs4_acl)
            print("with:\t%s" % with_nfs4_acl)
            print("after:\t%s" % after_nfs4_acl)
            raise e

    def test_prevention_perm_removal_of_file(self):
        from nfs4_share.manage import create, delete
        source = self.fabricate([
            "file"
        ])
        items = [j(source, 'file')]
        share = create(j(self.working_dir, 'share'), items=items, managing_groups=[self.calling_prim_group],
                       domain="op.umcutrecht.nl")
        os.remove(items[0])  # Remove original file
        self.assertFalse(os.path.exists(items[0]))  # Ensure it is gone

        # Try deleting the share without a force
        logging.disable(logging.ERROR)  # to hide the ERROR being logged on the next level
        self.assertRaises(FileNotFoundError, delete, share.directory)
        logging.disable(logging.NOTSET)  # re-enable full logging
        # Make sure the file is still in the share
        self.assertTrue(os.path.exists(j(share.directory, 'file')))

        # Retry with force applied
        delete(share.directory, force=True)

        self.assertFalse(os.path.exists(j(share.directory, 'file')))

    def test_removing_file_instead_of_share(self):
        from nfs4_share.manage import create, delete
        from nfs4_share.share import IllegalShareSetupError
        source = self.fabricate([
            "file"
        ])
        items = [j(source, 'file')]
        share = create(j(self.working_dir, 'share'), items=items, managing_groups=[self.calling_prim_group],
                       domain="op.umcutrecht.nl")
        with self.assertRaises(IllegalShareSetupError):
            delete(j(share.directory, 'file'))
        self.assertTrue(os.path.exists(j(share.directory, 'file')))
