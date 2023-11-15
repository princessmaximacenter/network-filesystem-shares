import pytest
import re
import os
from pathlib import Path

from src.nfs4_share import track_changes
from src.nfs4_share.manage import add,delete
from .utils import fabricate_a_source

# helper functions #

def read_tracking_file(track_changes_dir:Path, share_name:str, files_or_users:str):
    """Read txt file used to track user or item changes"""
    with open(Path(track_changes_dir, f'{share_name}_{files_or_users}.txt'), 'r') as f:
        tracked_items = f.readlines()
    tracked_items = [line.strip() for line in tracked_items]
    tracked_items = sorted(list(set(tracked_items)))
    return tracked_items

def get_last_n_commit_msgs(repo, branch, n):
    """Retrieve last n git commit message"""
    commits = list(repo.iter_commits(branch, max_count=n))
    commit_msgs = [commit.message.strip() for commit in commits]
    return commit_msgs

# tests #

@pytest.fixture(scope="module")
def track_changes_dir(tmpdir_factory):
    """Create a temporary directory to test track changes functionality"""
    return tmpdir_factory.mktemp("tc")

@pytest.fixture(scope='module')
def track_changes_repo(track_changes_dir):
    """run git init in track_changes_dir"""
    repo = track_changes.initialize_track_changes_dir(track_changes_dir)
    return repo

def test_initialize_user_tracking(single_file_share, track_changes_repo, calling_user, calling_prim_group, variables):
    share_name = Path(single_file_share.directory).name
    add(single_file_share.directory, track_change_dir=Path(track_changes_repo.working_dir))

    # expected values
    expected_commit_msg = f'[{share_name}]User change tracking initialized'
    expected_tracked_users = [variables["group_directive"].format(calling_prim_group),
                              variables["user_directive"].format(calling_user)]
    expected_tracked_users = [re.sub('Require.*(?=ldap)','',user) for user in expected_tracked_users]
    
    # test values
    # user and item list initializations are done at the same time, thus get last 2 commits
    commit_msgs = get_last_n_commit_msgs(track_changes_repo, 'HEAD', 2)
    tracked_users = read_tracking_file(track_changes_repo.working_dir, share_name, 'users')

    assert expected_commit_msg in commit_msgs and tracked_users == expected_tracked_users

def test_initialize_item_tracking(single_file_share, track_changes_repo):
    share_name = Path(single_file_share.directory).name
    add(single_file_share.directory, track_change_dir=Path(track_changes_repo.working_dir))

    # expected values
    expected_commit_msg = f'[{share_name}]File change tracking initialized'
    expected_tracked_items = sorted(list(set(os.listdir(single_file_share.directory)) - {'.htaccess.files.bioinf'}))

    # test values
    # user and item list initializations are done at the same time, thus get last 2 commits
    commit_msgs = get_last_n_commit_msgs(track_changes_repo, 'HEAD', 2)
    tracked_items = read_tracking_file(track_changes_repo.working_dir, share_name, 'files')

    assert expected_commit_msg in commit_msgs and tracked_items == expected_tracked_items


def test_item_add_tracking(single_file_share, source_dir, track_changes_repo):
    items = fabricate_a_source(source_dir, ['file1'])
    share_name = Path(single_file_share.directory).name
    add(single_file_share.directory, items=items, track_change_dir=Path(track_changes_repo.working_dir))
    
    # expected values
    expected_tracked_items = sorted(list(set(os.listdir(single_file_share.directory)) - {'.htaccess.files.bioinf'}))
    expected_last_commit = f'[{share_name}][ITEM][ADDED]{len(items)} item(s)'

    # test values
    tracked_items = read_tracking_file(track_changes_repo.working_dir, share_name, 'files')
    last_commit = track_changes_repo.head.commit.message

    assert (tracked_items, last_commit) == (expected_tracked_items, expected_last_commit)

def test_item_rm_tracking(single_file_share, source_dir, track_changes_repo):
    share_name = Path(single_file_share.directory).name
    items = fabricate_a_source(source_dir, ['file1'])
    add(single_file_share.directory, items=items, track_change_dir=Path(track_changes_repo.working_dir))
    
    # expected output after deletion
    # expected shared items = original share items excluding removed file1 and htaccess file
    expected_tracked_items = sorted(list(set(os.listdir(single_file_share.directory)) - {'.htaccess.files.bioinf', 'file1'}))
    expected_commit_msg = f'[{share_name}][ITEM][REMOVED]{len(items)} item(s)'

    # collect information after deletion
    delete(single_file_share.directory, items=['file1'], track_change_dir=Path(track_changes_repo.working_dir))
    tracked_items = read_tracking_file(track_changes_repo.working_dir, share_name, 'files')
    last_commit = track_changes_repo.head.commit.message

    assert (tracked_items, last_commit) == (expected_tracked_items, expected_commit_msg)

def test_user_add_tracking(single_file_share, track_changes_repo, calling_user, calling_prim_group, variables):
    share_name = Path(single_file_share.directory).name

    # expected values
    extra_users_ldap = [variables["user_directive"].format(user) for user in variables["multiple_new_users"]] 
    extra_users_ldap = [re.sub('Require.*(?=ldap)','',user) for user in extra_users_ldap]
    expected_tracked_users = read_tracking_file(track_changes_repo.working_dir, share_name, 'users') + extra_users_ldap
    expected_commit_msg = f'[{share_name}][USER][ADDED]{",".join(sorted(extra_users_ldap))}'
    
    # test values
    add(single_file_share.directory,users=variables["multiple_new_users"], 
        domain=variables["domain_name"], lock=True, user_apache_directive=variables["user_directive"],
        group_apache_directive=variables["group_directive"], 
        track_change_dir=Path(track_changes_repo.working_dir))
    
    tracked_users = read_tracking_file(track_changes_repo.working_dir, share_name, 'users')
    last_commit = track_changes_repo.head.commit.message

    assert (last_commit, sorted(tracked_users)) == (expected_commit_msg, sorted(expected_tracked_users))

def test_user_rm_tracking(single_file_share, track_changes_repo, variables):
    share_name = Path(single_file_share.directory).name
    add(single_file_share.directory,users=variables["multiple_new_users"], 
        domain=variables["domain_name"], lock=True, user_apache_directive=variables["user_directive"],
        group_apache_directive=variables["group_directive"], 
        track_change_dir=Path(track_changes_repo.working_dir))

    # expected values
    rm_users_ldap = variables["user_directive"].format(variables["user_to_rm_from_share"]) 
    rm_users_ldap = [re.sub('Require.*(?=ldap)','',rm_users_ldap)]
    expected_tracked_users = set(read_tracking_file(track_changes_repo.working_dir, share_name, 'users')) - set(rm_users_ldap)
    expected_commit_msg = f'[{share_name}][USER][REMOVED]{",".join(rm_users_ldap)}'
    
    # test values
    delete(single_file_share.directory, domain=variables["domain_name"], 
           users=[variables["user_to_rm_from_share"]], lock=True,
           track_change_dir=Path(track_changes_repo.working_dir))
    tracked_users = read_tracking_file(track_changes_repo.working_dir, share_name, 'users')
    last_commit = track_changes_repo.head.commit.message

    assert (last_commit, sorted(tracked_users)) == (expected_commit_msg, sorted(list(expected_tracked_users)))

def test_share_rm_tracking(single_file_share, track_changes_repo):
    share_name = Path(single_file_share.directory).name

    # expected values
    expected_commit_msg = f'[{share_name}][SHARE][REMOVED]'
    expected_tracking_files = set(os.listdir(track_changes_repo.working_dir))-{f'{share_name}_files.txt', f'{share_name}_users.txt'}
    
    # test values
    delete(single_file_share.directory, track_change_dir=Path(track_changes_repo.working_dir))
    last_commit = track_changes_repo.head.commit.message
    tracking_files = set(os.listdir(track_changes_repo.working_dir))

    assert (last_commit, sorted(tracking_files)) == (expected_commit_msg, sorted(expected_tracking_files))