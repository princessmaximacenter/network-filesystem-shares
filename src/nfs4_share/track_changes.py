from git import Repo
from git.exc import InvalidGitRepositoryError
import re
from pathlib import Path
import logging
import os

def initialize_track_changes_dir(track_change_dir:Path):
    """
    Run git init in a directory for tracking changes if it's not done already
    """
    if not track_change_dir.exists():
        logging.info(f'Creating track changes dir: {track_change_dir}')
        os.mkdir(track_change_dir)
    try:
        repo=Repo(track_change_dir)
        logging.debug(f'Tracking changes in {track_change_dir}')
    except InvalidGitRepositoryError:
        logging.info(f'Running git init in {track_change_dir}')
        repo=Repo.init(track_change_dir)
    return repo

def initialize_file_list(track_change_dir, share_directory):
    """
    Create a txt file to track item changes in a share
    """
    filelist_txt=Path(track_change_dir, f"{Path(share_directory).name}_files.txt")
    if not filelist_txt.exists():
        filelist=os.listdir(share_directory)
        filelist=[item for item in filelist if item != ".htaccess.files.bioinf"]
        with open(filelist_txt, 'w') as tc_file:
            for item in filelist:
                tc_file.write(item+'\n')
        commit_msg=f'[{Path(share_directory).name}]File change tracking initialized'
        logging.info(commit_msg)
        stage_and_commit(track_change_dir, filelist_txt, commit_msg)

def initialize_user_list(track_change_dir, share_directory):
    """
    Create a txt file to track user changes in a share
    """
    userlist_txt=Path(track_change_dir, f"{Path(share_directory).name}_users.txt")
    if not userlist_txt.exists():
        try:
            with open(Path(share_directory,'.htaccess.files.bioinf'), 'r') as htaccess_file:
                lines=htaccess_file.readlines()
                htaccess_list=[re.sub('Require.*(?=ldap)','',l) for l in lines if 'ldap' in l]
                htaccess_list=[l.strip() for l in htaccess_list]
                htaccess_list.sort()
        except FileNotFoundError:
            htaccess_list=[]
        with open(userlist_txt, 'w') as tc_file:
            for htaccess in htaccess_list:
                tc_file.write(htaccess+'\n')
        commit_msg=f'[{Path(share_directory).name}]User change tracking initialized'
        logging.info(commit_msg)
        stage_and_commit(track_change_dir, userlist_txt, commit_msg)


def track_user_addition(track_change_dir, share_directory):
    """
    read and update user list from htaccess file of a share
    """
    # Read htaccess file and sort entries
    with open(Path(share_directory,'.htaccess.files.bioinf'), 'r') as htaccess_file:
        lines=htaccess_file.readlines()
        htaccess=[re.sub('Require.*(?=ldap)','',l) for l in lines if 'ldap' in l]
        htaccess=[l.strip() for l in htaccess]
        htaccess.sort()

    # Check the list of existing users in the track changes dir
    userlist_txt=Path(track_change_dir, f"{Path(share_directory).name}_users.txt")
    if userlist_txt.exists():
        with open(userlist_txt, 'r') as tc_file:
            previous_htaccess=tc_file.readlines()
            previous_htaccess=[l.strip() for l in previous_htaccess]
    else:
        previous_htaccess=[]
    
    # Update userlist if new user(s) are added
    new_users=set(htaccess)-set(previous_htaccess)
    if len(new_users) > 0:
        with open(userlist_txt, 'a') as tc_file:
            for item in new_users:
                tc_file.write(item+'\n')
        commit_msg=f'[{Path(share_directory).name}][USER][ADDED]{",".join(sorted(new_users))}'
        stage_and_commit(track_change_dir, userlist_txt, commit_msg)
        logging.info(commit_msg)
    else:
        logging.info(f'No user access changes in {Path(share_directory).name}')

def track_file_addition(track_change_dir, share_directory, new_items):
    """
    Function to update file list. This relies on existing code to check if all files are indeed new.
    """
    # update file list if there are new item(s) added
    if len(new_items)>0:
        filelist_txt=Path(track_change_dir, f"{Path(share_directory).name}_files.txt")
        with open(filelist_txt, 'a') as tc_file:
            for item in new_items:
                basename_item=Path(item).name
                tc_file.write(basename_item+'\n')

        # Note changes in commit message
        commit_msg=f'[{Path(share_directory).name}][ITEM][ADDED]{str(len(new_items))} item(s)'
        stage_and_commit(track_change_dir,filelist_txt,commit_msg)
        logging.info(commit_msg)
    else:
        logging.info(f'No new files added to {Path(share_directory).name}')

def track_share_deletion(track_change_dir, share_directory):
    repo = Repo(track_change_dir)
    tc_files=[f"{Path(share_directory).name}_files.txt",
              f"{Path(share_directory).name}_users.txt"]
    repo.index.remove(tc_files)
    for f in tc_files:
        if os.path.exists(Path(track_change_dir,f)):
            os.remove(Path(track_change_dir,f))
    commit_msg=f'[{Path(share_directory).name}][SHARE][REMOVED]'
    repo.index.commit(commit_msg)
    logging.info(commit_msg)

def track_file_deletion(track_change_dir, share_directory, deleted_items):
    filelist_txt=Path(track_change_dir, f"{Path(share_directory).name}_files.txt")
    # read existing file list
    with open(filelist_txt, 'r') as tc_file:
        previous_filelist=tc_file.readlines()
        previous_filelist=[l.strip() for l in previous_filelist]
    
    # remove deleted items from file list
    deleted_items=[Path(item).name for item in deleted_items]
    updated_filelist=[file for file in previous_filelist if file not in deleted_items]

    # rewrite filelist_txt
    with open(filelist_txt, 'w') as tc_file:
        for item in updated_filelist:
            basename_item=Path(item).name
            tc_file.write(basename_item+'\n')

    # keep track of changes with git
    commit_msg=f'[{Path(share_directory).name}][ITEM][REMOVED]{str(len(deleted_items))} item(s)'
    logging.info(commit_msg)
    stage_and_commit(track_change_dir, filelist_txt, commit_msg)

def track_user_removal(track_change_dir, share_directory, deleted_users):
    userlist_txt=Path(track_change_dir, f"{Path(share_directory).name}_users.txt")
    with open(userlist_txt, 'r') as tc_file:
        previous_htaccess=tc_file.readlines()
        previous_htaccess=[l.strip() for l in previous_htaccess]
    
    # get a list of current user from git-tracked userlist
    current_htaccess=[l for l in previous_htaccess if not re.search(rf'\b({"|".join(deleted_users)})\b', l)]

    # remove deleted users from git-tracked userlist
    if deleted_users:
        removed_htaccess=set(previous_htaccess)-set(current_htaccess)
        with open(userlist_txt, 'w') as tc_file:
            for item in current_htaccess:
                tc_file.write(item+'\n')
        commit_msg=f'[{Path(share_directory).name}][USER][REMOVED]{",".join(sorted(removed_htaccess))}'
        stage_and_commit(track_change_dir, userlist_txt, commit_msg)
        logging.info(commit_msg)
    else:
        logging.info(f'No user access changes in {Path(share_directory).name}')

def stage_and_commit(track_change_dir, filename, commit_msg):
    """
    Function to stage and commit changes to list files
    """
    repo = initialize_track_changes_dir(track_change_dir)
    repo.index.add(filename)
    repo.index.commit(commit_msg)
    