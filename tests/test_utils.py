import os
from tests.base_test import TestBase


class TestPermissions(TestBase):

    def test_string_to_ace(self):
        import nfs4_share.acl as nfs4_acl
        ace = nfs4_acl.AccessControlEntity(entry_type='A',
                                           flags='fd',
                                           identity=self.calling_user,
                                           domain="op.umcutrecht.nl",
                                           permissions='rwadxtTnNcCoy')
        re_ace = nfs4_acl.AccessControlEntity.from_string("A:fd:%s@op.umcutrecht.nl:rwadxtTnNcCoy" % self.calling_user)
        self.assertEqual(ace, re_ace)

    def test_permissions_via_loop_set_get(self):
        import nfs4_share.acl as nfs4_acl
        try:
            nfs4_acl.assert_command_exists(nfs4_acl.getfacl_bin)
            nfs4_acl.assert_command_exists(nfs4_acl.getfacl_bin)
        except AssertionError:
            self.skipTest("nfs4 ACLs are required for this test")

        fn = os.path.join(self.working_dir, 'file')
        with open(fn, 'w') as f:
            f.write('foo')
        ace = nfs4_acl.AccessControlEntity(entry_type='A',
                                           flags='fd',
                                           identity=self.calling_user,
                                           domain="op.umcutrecht.nl",
                                           permissions='rwadxtTnNcCoy')
        acl = nfs4_acl.AccessControlList([ace])
        acl.set(fn)
        actual_acl = nfs4_acl.AccessControlList.from_file(fn)
        self.assertEqual(acl, actual_acl)

    def test_equality_permissions_shuffle(self):
        from nfs4_share.acl import AccessControlList, AccessControlEntity
        ace1 = AccessControlEntity(entry_type='A',
                                   flags='fd',
                                   identity=self.calling_user,
                                   domain="op.umcutrecht.nl",
                                   permissions='rwadxtTnNcCoy')
        ace2 = AccessControlEntity(entry_type='A',
                                   flags='fd',
                                   identity=self.calling_user,
                                   domain="op.umcutrecht.nl",
                                   permissions='awrdxtTnNcCoy')
        self.assertEqual(ace1, ace2)
        self.assertEqual(AccessControlList(ace1), AccessControlList(ace2))

        ace1 = AccessControlEntity(entry_type='A',
                                   flags='fd',
                                   identity=self.calling_user,
                                   domain="op.umcutrecht.nl",
                                   permissions='rwadxtTnNcCo')
        ace2 = AccessControlEntity(entry_type='A',
                                   flags='fd',
                                   identity=self.calling_user,
                                   domain="op.umcutrecht.nl",
                                   permissions='awrdxtTnNcCoy')
        self.assertNotEqual(ace1, ace2)
        self.assertNotEqual(AccessControlList(ace1), AccessControlList(ace2))

        ace1 = AccessControlEntity(entry_type='A',
                                   flags='fd',
                                   identity="hkerstens",
                                   domain="op.umcutrecht.nl",
                                   permissions='rwadxtTnNcCo')
        ace2 = AccessControlEntity(entry_type='A',
                                   flags='fd',
                                   identity=self.calling_user,
                                   domain="op.umcutrecht.nl",
                                   permissions='rwadxtTnNcCo')
        self.assertNotEqual(ace1, ace2)
        self.assertNotEqual(AccessControlList(ace1), AccessControlList(ace2))

    def test_acl_minus_acl(self):
        import nfs4_share.acl as nfs4_acl
        share_entries = [nfs4_acl.AccessControlEntity(entry_type='A',
                                                      flags='',
                                                      identity=self.calling_user,
                                                      domain="op.umcutrecht.nl",
                                                      permissions='rwadxtTnNcCoy'),
                         nfs4_acl.AccessControlEntity(entry_type='A',
                                                      flags='g',
                                                      identity=self.calling_prim_group,
                                                      domain="op.umcutrecht.nl",
                                                      permissions='rwadxtTnNcCoy')]
        pre_entries = [nfs4_acl.AccessControlEntity(entry_type='A',
                                                    flags='',
                                                    identity="hkerstens",
                                                    domain="op.umcutrecht.nl",
                                                    permissions='rwadxtTnNcCoy'),
                       nfs4_acl.AccessControlEntity(entry_type='A',
                                                    flags='',
                                                    identity=self.calling_user,
                                                    domain="op.umcutrecht.nl",
                                                    permissions='rwadxtTnNcCoy'),
                       nfs4_acl.AccessControlEntity(entry_type='A',
                                                    flags='g',
                                                    identity=self.calling_prim_group,
                                                    domain="op.umcutrecht.nl",
                                                    permissions='rwadxtTnNcCoy')]

        pre_share_acl = nfs4_acl.AccessControlList(pre_entries + pre_entries)
        with_share_acl = nfs4_acl.AccessControlList(pre_entries + share_entries + pre_entries)
        share_removed_acl = with_share_acl - nfs4_acl.AccessControlList(share_entries)
        try:
            self.assertEqual(pre_share_acl.entries, share_removed_acl.entries)
        except AssertionError as e:
            print(pre_share_acl.entries)
            print(with_share_acl.entries)
            print(share_removed_acl.entries)
            raise e

    def test_importing_api(self):
        from nfs4_share.manage import create, delete
        type(create)
        type(delete)
