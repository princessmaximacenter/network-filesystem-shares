import pytest
import pwd
import grp
import os
from .utils import fabricate_a_source

@pytest.fixture(scope="session")
def calling_user() -> str:
    return pwd.getpwuid(os.getuid())[0]


@pytest.fixture(scope="session")
def calling_prim_group() -> str:
    return grp.getgrgid(os.getgid())[0]


@pytest.fixture(scope="function")
def source_dir(tmpdir_factory):
    return tmpdir_factory.mktemp("source")


@pytest.fixture(scope="function")
def shares_dir(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp("shares")
    yield tmpdir
    from nfs4_share.manage import unlock

    for share in os.listdir(tmpdir):
        unlock(tmpdir.join(share))

@pytest.fixture(scope='function')
def single_file_share(source_dir, shares_dir, calling_user, calling_prim_group, variables):
    from nfs4_share.manage import create
    items = fabricate_a_source(source_dir, [
        "file"
    ])
    share = create(shares_dir.join('share'), items=items, users=[calling_user], managing_groups=[calling_prim_group],
                   user_apache_directive=variables["user_directive"], group_apache_directive=variables["group_directive"],
                   domain=variables["domain_name"],
                   service_application_accounts=variables['service_application_accounts'])
    return share