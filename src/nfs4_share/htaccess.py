
import os
import logging
import warnings
import parse
from .share import Share


def create_at(share, users, user_directive_template, groups, group_directive_template,
              filename='.htaccess.files.bioinf'):
    """
    Creates an .htaccess (or alternative filename) to give access for an apache server to provide access to a share
    """
    htaccess = ['<RequireAny>']
    for user in users:
        htaccess.append(user_directive_template.format(user))
    for group in groups:
        htaccess.append(group_directive_template.format(group))
    htaccess.append('</RequireAny>')
    htaccess_file_path = os.path.join(share.directory, filename)
    with open(htaccess_file_path, 'w') as f:
        for line in htaccess:
            f.write("%s\n" % line)
    share.permissions.set(htaccess_file_path)
    logging.debug("Generated and placed htaccess file at %s: %s" % (htaccess_file_path, htaccess))


def append_at(share: Share, users: list, user_directive_template: str, groups: list, group_directive_template: str,
              filename: str = '.htaccess.files.bioinf'):
    """
    Creates a new .htaccess file containing the existing users/groups plus the new ones.
    WARNING: the directive_template has to be the same as the one used during creation otherwise you might lose
    permissions for some users/groups
    """
    # Try to extract existing htaccess users and groups
    try:
        # Create path to htaccess file
        htaccess_file_path = os.path.join(share.directory, filename)
        # Try to open it
        with open(htaccess_file_path, 'r') as htaccess_file:
            htaccess_lines = htaccess_file.readlines()
        # Remove unwanted characters
        htaccess_lines = [line.strip() for line in htaccess_lines]
        # extract users and groups
        users += extract_targets(htaccess_lines, user_directive_template)
        groups += extract_targets(htaccess_lines, group_directive_template)
    except FileNotFoundError:
        warnings.warn(f"No file found called {filename} to append new users/groups to, will create it instead.")

    # Recreate htaccess file
    # list(set()) just to make sure the list is unique to avoid duplications
    create_at(share, list(set(users)), user_directive_template, list(set(groups)), group_directive_template, filename)


def extract_targets(lines: list, format_string: str):
    """ Function to extract values used during formatting of a string

    :param lines: List of strings to search in
    :param format_string: Format string used in the past to parse values into a string
    :return: list of values found with the parse function
    """
    found_targets = []
    for line in lines:
        parsed = parse.parse(format_string, line)
        if parsed is not None:
            found_targets += list(parsed)
    return found_targets


def remove_from(share, filename='.htaccess.files.bioinf', absent_ok=False):
    """
        Removes an .htaccess (or alternative filename) to give access for an apache server to provide access to a share
    """
    logging.debug("Removing access file at %s: %s" % (share.directory, filename))
    htaccess = os.path.join(share.directory, filename)
    if os.path.exists(htaccess):
        os.remove(htaccess)
    elif not absent_ok:
        logging.warning("Could not locate htaccess file: %s" % os.path.join(share.directory, filename))
