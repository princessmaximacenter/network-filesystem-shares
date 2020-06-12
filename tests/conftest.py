import pytest
import pwd
import grp
import os


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
