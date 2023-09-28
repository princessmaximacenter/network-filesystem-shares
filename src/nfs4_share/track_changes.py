from git import Repo
import re
from pathlib import Path
import logging

def check_and_update_user_list(track_change_dir, share_directory):
    """
    read and update user list from htaccess file of a share
    """
    # Read htaccess file and sort entries
    with open(Path(share_directory,'.htaccess.files.bioinf'), 'r') as htaccess_file:
        lines=htaccess_file.readlines()
        htaccess=[re.sub('Require.*(?=ldap)','',l) for l in lines if 'ldap' in l]
        htaccess=[l.strip() for l in htaccess]
        htaccess.sort()

    # Check for a list of existing users
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
            commit_msg=f'Added {",".join(new_users)} to {Path(share_directory).name}'
            stage_and_commit(track_change_dir, userlist_txt, commit_msg)
            logging.info(commit_msg)
    else:
        logging.info(f'No user access changes in {Path(share_directory).name}')

def update_filelist(track_change_dir, share_directory, new_items):
    """
    Function to update file list. This relies on existing code to check if all files are indeed new.
    """
    # update file list if there are new item(s) added
    if len(new_items)>0:
        filelist_txt=Path(track_change_dir, f"{Path(share_directory).name}_files.txt")
        with open(filelist_txt, 'a') as tc_file:
            for item in new_items:
                tc_file.write(item+'\n')

        # Note changes in commit message
        commit_msg=f'Added {str(len(new_items))} item(s) to {Path(share_directory).name}'
        stage_and_commit(track_change_dir,filelist_txt,commit_msg)
        logging.info(commit_msg)
    else:
        logging.info(f'No new files added to {Path(share_directory).name}')

def stage_and_commit(track_change_dir, filename, commit_msg):
    """
    Function to stage and commit changes to list files
    """
    repo = Repo(track_change_dir)
    repo.index.add(filename)
    repo.index.commit(commit_msg)

# QUERY CHANGES
# get 
# git diff 1a8b1e62bbcac43a5f71950fdcb3e74b311f9717 HEAD -U0