
import os
import logging


def create_at(share, users, user_directive_template, groups, group_directive_template, filename='.htaccess.files.bioinf'):
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
