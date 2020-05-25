import os

from os.path import join as j
from tests.base_test import TestBase


class TestLocking(TestBase):

    def test_lock_on_single_file(self):
        from nfs4_share.manage import create, delete
        source = self.fabricate([
            "file"
        ])
        items = [j(source, 'file')]
        share = create(j(self.working_dir, 'share'), items=items, managing_groups=[self.calling_prim_group],
                       domain="op.umcutrecht.nl")
        self.assertRaises(PermissionError, os.remove, j(share.directory, "file"))
        self.assertTrue(os.path.exists(j(share.directory, "file")))
        delete(j(self.working_dir, 'share'))
        self.assertFalse(os.path.exists(j(share.directory, "file")))
