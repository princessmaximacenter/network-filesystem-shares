import pytest


def test_string_to_ace(calling_user):
    import nfs4_share.acl as nfs4_acl
    ace = nfs4_acl.AccessControlEntity(entry_type='A',
                                       flags='fd',
                                       identity=calling_user,
                                       domain="op.umcutrecht.nl",
                                       permissions='rwadxtTnNcCoy')
    re_ace = nfs4_acl.AccessControlEntity.from_string("A:fd:%s@op.umcutrecht.nl:rwadxtTnNcCoy" % calling_user)
    assert ace == re_ace


def test_permissions_via_loop_set_get(calling_user, source_dir):
    import nfs4_share.acl as nfs4_acl
    try:
        nfs4_acl.assert_command_exists(nfs4_acl.getfacl_bin)
        nfs4_acl.assert_command_exists(nfs4_acl.getfacl_bin)
    except AssertionError:
        pytest.skip("nfs4 ACLs are required for this test")

    fn = source_dir.join('file')
    with open(fn, 'w') as f:
        f.write('foo')
    ace = nfs4_acl.AccessControlEntity(entry_type='A',
                                       flags='fd',
                                       identity=calling_user,
                                       domain="op.umcutrecht.nl",
                                       permissions='rwadxtTnNcCoy')
    acl = nfs4_acl.AccessControlList([ace])
    acl.set(fn)
    actual_acl = nfs4_acl.AccessControlList.from_file(fn)
    acl == actual_acl


def test_equality_permissions_shuffle(calling_user):
    from nfs4_share.acl import AccessControlList, AccessControlEntity
    ace1 = AccessControlEntity(entry_type='A',
                               flags='fd',
                               identity=calling_user,
                               domain="op.umcutrecht.nl",
                               permissions='rwadxtTnNcCoy')
    ace2 = AccessControlEntity(entry_type='A',
                               flags='fd',
                               identity=calling_user,
                               domain="op.umcutrecht.nl",
                               permissions='awrdxtTnNcCoy')
    assert ace1 == ace2
    assert AccessControlList(ace1) == AccessControlList(ace2)

    ace3 = AccessControlEntity(entry_type='A',
                               flags='fd',
                               identity=calling_user,
                               domain="op.umcutrecht.nl",
                               permissions='rwadxtTnNcCo')
    ace4 = AccessControlEntity(entry_type='A',
                               flags='fd',
                               identity=calling_user,
                               domain="op.umcutrecht.nl",
                               permissions='awrdxtTnNcCoy')
    assert ace3 != ace4
    assert AccessControlList(ace3) != AccessControlList(ace4)

    ace5 = AccessControlEntity(entry_type='A',
                               flags='fd',
                               identity="hkerstens",
                               domain="op.umcutrecht.nl",
                               permissions='rwadxtTnNcCo')
    ace6 = AccessControlEntity(entry_type='A',
                               flags='fd',
                               identity=calling_user,
                               domain="op.umcutrecht.nl",
                               permissions='rwadxtTnNcCo')
    assert ace5 != ace6
    assert AccessControlList(ace5) != AccessControlList(ace6)


def test_acl_minus_acl(calling_user, calling_prim_group):
    import nfs4_share.acl as nfs4_acl
    share_entries = [nfs4_acl.AccessControlEntity(entry_type='A',
                                                  flags='',
                                                  identity=calling_user,
                                                  domain="op.umcutrecht.nl",
                                                  permissions='rwadxtTnNcCoy'),
                     nfs4_acl.AccessControlEntity(entry_type='A',
                                                  flags='g',
                                                  identity=calling_prim_group,
                                                  domain="op.umcutrecht.nl",
                                                  permissions='rwadxtTnNcCoy')]
    pre_entries = [nfs4_acl.AccessControlEntity(entry_type='A',
                                                flags='',
                                                identity="hkerstens",
                                                domain="op.umcutrecht.nl",
                                                permissions='rwadxtTnNcCoy'),
                   nfs4_acl.AccessControlEntity(entry_type='A',
                                                flags='',
                                                identity=calling_user,
                                                domain="op.umcutrecht.nl",
                                                permissions='rwadxtTnNcCoy'),
                   nfs4_acl.AccessControlEntity(entry_type='A',
                                                flags='g',
                                                identity=calling_prim_group,
                                                domain="op.umcutrecht.nl",
                                                permissions='rwadxtTnNcCoy')]

    pre_share_acl = nfs4_acl.AccessControlList(pre_entries + pre_entries)
    with_share_acl = nfs4_acl.AccessControlList(pre_entries + share_entries + pre_entries)
    share_removed_acl = with_share_acl - nfs4_acl.AccessControlList(share_entries)
    try:
        assert pre_share_acl.entries == share_removed_acl.entries
    except AssertionError as e:
        print(pre_share_acl.entries)
        print(with_share_acl.entries)
        print(share_removed_acl.entries)
        raise e


def test_importing_api():
    from nfs4_share.manage import create, delete
    type(create)
    type(delete)
