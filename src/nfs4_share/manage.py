#!/usr/bin/env python3

import logging
import pwd
import grp
import os

from pathlib import Path
from . import htaccess
from .share import Share
from .acl import AccessControlList, AccessControlEntity
from . import track_changes

def create(share_directory, domain, user_apache_directive="{}", group_apache_directive="{}",
           items=None, users=None, groups=None, managing_users=None, managing_groups=None, lock=True,
           service_application_accounts=None, track_change_dir=None):
    """
    Creates a share. The directory representing the share should be non-existent.
            For more information on input variables run ./share remove --help
    """
    # Ugly, but best practice to default to empty lists as follows:
    if items is None:
        items = []
    if users is None:
        users = []
    if groups is None:
        groups = []
    if managing_users is None and managing_groups is None:
        msg = "A share needs to have either a managing user or group!"
        logging.error(msg)
        raise RuntimeError(msg)
    if managing_users is None:
        managing_users = []
    if managing_groups is None:
        managing_groups = []
    if service_application_accounts is None:
        service_application_accounts = []
    ensure_users_exist(users + managing_users + service_application_accounts)
    ensure_groups_exist(groups + managing_groups)
    ensure_items_exist(items)
    try:
        share = Share(share_directory)
        if track_change_dir is not None:
            track_changes.initialize_file_list(track_change_dir, share_directory)
            track_changes.initialize_user_list(track_change_dir, share_directory)
    except FileExistsError as e:
        logging.exception('Share directory %s already exists!' % share_directory)  # Stack traces by default
        raise e
    share.permissions = generate_permissions(users=users + service_application_accounts,
                                             groups=groups,
                                             managing_users=managing_users,
                                             managing_groups=managing_groups,
                                             domain=domain,
                                             manage_permissions=share.MANAGE_PERMISSION_UNLOCK)
    new_items=share.add(items)
    htaccess.create_at(share=share,
                       users=users + managing_users,
                       user_directive_template=user_apache_directive,
                       groups=groups + managing_groups,
                       group_directive_template=group_apache_directive)
    
    if track_change_dir is not None:
        track_changes.track_file_addition(track_change_dir, share_directory, new_items)
        track_changes.track_user_addition(track_change_dir, share_directory)
        logging.info(f'Updated shares info in {track_change_dir}')

    logging.info("Finished creating share at %s" % share.directory)
    if lock:
        share.lock()
    return share


def add(share_directory, user_apache_directive="{}", group_apache_directive="{}", domain=None, items=None, users=None,
        groups=None, managing_users=None, managing_groups=None, lock=False, service_application_accounts=None, track_change_dir=None):
    """
        Updates a share. The directory representing the share should exist.
            For more information on input variables run nfs4_share add --help
    """
    # Ugly, but best practice to default to empty lists as follows:
    if items is None:
        items = []
    if users is None:
        users = []
    if groups is None:
        groups = []
    if managing_users is None:
        managing_users = []
    if managing_groups is None:
        managing_groups = []
    if service_application_accounts is None:
        service_application_accounts = []
    ensure_users_exist(users)
    ensure_groups_exist(groups)
    ensure_items_exist(items)
    share = Share(share_directory, exist_ok=True)
    
    # create an initial file list for tracking changes if the list is not in track change dir yet
    if track_change_dir is not None:
        track_changes.initialize_file_list(track_change_dir, share_directory)
        track_changes.initialize_user_list(track_change_dir, share_directory)

    # Just to be sure,unlock the share (does no harm if no locked)
    share.unlock()
    if items:
        new_items=share.add(items)
        if track_change_dir is not None:
            track_changes.track_file_addition(track_change_dir, share_directory, new_items)
            logging.info(f'Updated shares info in {track_change_dir}')

    # Add the users
    if users or groups:
        assert domain, "domain cannot be left empty if trying to add users or groups"
        htaccess.append_at(share=share,
                           users=users + managing_users,
                           user_directive_template=user_apache_directive,
                           groups=groups + managing_groups,
                           group_directive_template=group_apache_directive)
        acl = share.permissions
        updated_acl = acl + generate_permissions(users=users + service_application_accounts,
                                                 groups=groups,
                                                 managing_groups=managing_groups,
                                                 managing_users=managing_users,
                                                 domain=domain,
                                                 manage_permissions=share.MANAGE_PERMISSION_UNLOCK)
        share.permissions = updated_acl

        if track_change_dir is not None:
            track_changes.track_user_addition(track_change_dir, share_directory)
            logging.info(f'Updated shares info in {track_change_dir}')

    if lock:
        share.lock()
    return share


def delete(share_directory, domain=None,
           force=False, items=None, users=None, groups=None,track_change_dir=None, lock=False):
    """
        Deletes a share. The directory representing the share should exist.
                 For more information on input variables run nfs4_share delete --help
    """
    share = unlock(share_directory)
    # create an initial file list for tracking changes if the list is not in track change dir yet
    if track_change_dir is not None:
        track_changes.initialize_file_list(track_change_dir, share_directory)
        track_changes.initialize_user_list(track_change_dir, share_directory)
    if items is None:
        items=[]
    if users is None:
        users=[]
    if groups is None:
        groups=[]

    if not users and not groups and not items:
        htaccess.remove_from(share, absent_ok=True)
        share.self_destruct(force_file_removal=force)
        logging.info("Removed share at %s" % share.directory)
        if track_change_dir is not None:
            track_changes.track_share_deletion(track_change_dir, share_directory)
        return
        
    if items:
        # just to be sure that we remove file from share and not somewhere else
        items=[Path(share_directory, Path(item).name) for item in items]
        share.remove_items(items, force)
        if track_change_dir is not None:
            track_changes.track_file_deletion(track_change_dir, share_directory,items)

    if users or groups:
        assert domain, "domain cannot be left empty if trying to remove users or groups"
        # update htaccess
        logging.info(f"Will attempt to remove {','.join(groups+users)} from {share_directory}")
        htaccess.remove_at(share=share,
                           target_users=users,
                           target_groups=groups)
        acl = share.permissions
        # only allow user/groups removal at the moment
        acl_tobe_removed=generate_permissions(users=users,
                                              groups=groups,
                                              managing_groups=[],
                                              managing_users=[],
                                              domain=domain,
                                              manage_permissions=share.MANAGE_PERMISSION_UNLOCK)
        share.permissions = AccessControlList(set(acl)-set(acl_tobe_removed))
        not_removed=[user.identity for user in list(set(acl_tobe_removed)-set(acl))]
        logging.debug(f'users not removed: {not_removed}')
        if not_removed:
            for entry in not_removed:
                logging.warning(f'{entry} ACL permission does not exist in {share_directory}')
        removed_users=list(set(users+groups)-set(not_removed))
        logging.info(f'Removed users: {removed_users}')
        if track_change_dir is not None:
            track_changes.track_user_removal(track_change_dir, share_directory, removed_users)
    if lock:
        share.lock()
    

def unlock(share_directory):
    """
        Unlocks a share. The directory representing the share should exist.
    """
    if not os.path.exists(share_directory):
        logging.error("\'%s\' is expected to exist!" % share_directory)
        raise FileNotFoundError(share_directory)
    share = Share(share_directory, exist_ok=True)
    share.unlock()
    return share


def ensure_users_exist(users):
    """
    Exits if one of the users does not exist
    """
    for user in users:
        try:
            pwd.getpwnam(user)
        except KeyError:
            raise RuntimeError('User %s does not exist!' % user)


def ensure_groups_exist(groups):
    """
    Exits if one of the groups does not exist
    """
    for group in groups:
        try:
            grp.getgrnam(group)
        except KeyError:
            raise RuntimeError('Group %s does not exist!' % group)


def ensure_items_exist(items):
    """
    Exits if one of the items does not exist
    """
    for item in items:
        if not os.path.exists(item):
            raise FileNotFoundError("Items '%s' does not exist! (%s)" % (os.path.basename(item), item))


def generate_permissions(users, groups, managing_users, managing_groups, domain, manage_permissions):
    """
    Builds and returns an Access Control List.
    """
    entries = []
    for user in users:
        user_ace = AccessControlEntity(entry_type='A',
                                       flags='',
                                       identity=user,
                                       domain=domain,
                                       permissions='rxtncy')
        entries.append(user_ace)
    for group in groups:
        group_ace = AccessControlEntity(entry_type='A',
                                        flags='g',
                                        identity=group,
                                        domain=domain,
                                        permissions='rxtncy')
        entries.append(group_ace)
    for user in managing_users:
        user_ace = AccessControlEntity(entry_type='A',
                                       flags='',
                                       identity=user,
                                       domain=domain,
                                       permissions=manage_permissions)
        entries.append(user_ace)
    for group in managing_groups:
        group_ace = AccessControlEntity(entry_type='A',
                                        flags='g',
                                        identity=group,
                                        domain=domain,
                                        permissions=manage_permissions)
        entries.append(group_ace)

    acl = AccessControlList(entries)
    logging.debug("Generated an access control list: %s" % repr(acl))
    return acl
