import logging
import os
import sys

from . acl import AccessControlList, AccessControlEntity


class Share:
    """
    Share object that is represented by a directory on the filesystem.

    Non-python Dependencies
    ------------
    Only works when creating shares on a NFSv4 filesystem.

    Needs the following binaries:
    * `/usr/bin/nfs4_setfacl`
    * `/usr/bin/nfs4_getfacl`
    """
    MANAGE_PERMISSION_LOCK = "rxaDdtTNcCo"
    MANAGE_PERMISSION_UNLOCK = "rwxaDdtTNcCo"

    def __init__(self, directory, exist_ok=False):
        self.directory = os.path.realpath(directory)
        if os.path.exists(directory):
            logging.debug("\'%s\' exists." % os.path.basename(directory))
        if os.path.exists(directory) and os.path.isfile(directory):
            raise IllegalShareSetupError("%s should be not non-existent or a directory!" % directory)
        os.makedirs(self.directory, exist_ok=exist_ok)

    def __repr__(self):
        return "Share({!r})".format(os.path.basename(self.directory))

    @property
    def permissions(self):
        return AccessControlList.from_file(self.directory)

    @permissions.setter
    def permissions(self, acl):
        logging.debug("Setting permissions on %s: %s" % (self.directory, acl))
        acl.set(self.directory)

    def add(self, items):
        """
        Adds items to the share
        """
        logging.debug("Adding items to %s: %s" % (self.directory, items))
        files = [i for i in items if os.path.isfile(i)]
        directories = [i for i in items if os.path.isdir(i)]
        # shared_items is used to get a final list of shared files
        # will be used to track filelist changes
        shared_items = items
        for file in files:
            target_file = os.path.join(self.directory, os.path.basename(file))
            # remove from shared items if file already exist in share
            shared_items = self._link_files(file, target_file, shared_items)
        for directory in directories:
            try:
                self._duplicate_as_linked_tree(directory)
            except FileExistsError as e:
                logging.debug("Directory %s already exists! Going to remove and re-add it!" % e.filename)
                # It is already there, either by having been added before or within an update
                self._unshare_linked_tree(e.filename)
                self._duplicate_as_linked_tree(directory)
                # remove source directory from new items, if they exist in the share
                shared_items.remove(directory)
        for unhandled_item in set(items) - set(directories).union(set(files)):
            shared_items.remove(unhandled_item)
            logging.error("Did not handle input item '%s'" % unhandled_item)
        return shared_items

    def _duplicate_as_linked_tree(self, source_root):
        """
        Traverses the directory tree, creating new directories but hard-linking files.
        """
        logging.debug("Started traversing %s \'s tree for file linkage and directory duplication." % self.directory)
        #  Create the containing directory that resides within the share
        within_share_dir_path = os.path.join(self.directory, os.path.basename(source_root))
        self._makedir(within_share_dir_path)
        for root, subdirectories, files in os.walk(source_root, followlinks=True):
            share_root = root.replace(str(source_root), within_share_dir_path, 1)
            for subdir in subdirectories:
                target = os.path.join(share_root, subdir)
                self._makedir(target)
            for file in files:
                source = os.path.join(root, file)
                target = os.path.join(share_root, file)
                self._link_files(source, target)

    def _unshare_linked_tree(self, directory, force_file_removal=False):
        """
        will have the share remove itself
        """
        logging.debug("Started traversing %s\'s tree from bottom up for un-sharing" % self.directory)
        for root, subdirectories, files in os.walk(directory, topdown=False, followlinks=True):
            for shared_file in files:
                self._unshare_file(os.path.join(root, shared_file), force=force_file_removal)
            for sub_dir in subdirectories:
                self._unshare_dir(os.path.join(root, sub_dir))
        os.rmdir(directory)

    def lock(self):
        """
        locks down the share for changing anything other than the access
        """
        logging.debug("Locking %s (and subdirectories)" % self.directory)
        self._adjust_manage_write_permissions(add_write=False)
        LOCK_ACL.append(target=self.directory)
        for subdirectory in self._subdirectories():
            LOCK_ACL.append(target=subdirectory)

    def unlock(self):
        """
        unlocks the share for changing anything other than the access
        """
        logging.debug("Unlocking %s (and subdirectories)" % self.directory)
        self._adjust_manage_write_permissions(add_write=True)
        LOCK_ACL.unset(target=self.directory)
        for subdirectory in self._subdirectories():
            LOCK_ACL.unset(target=subdirectory)

    def _adjust_manage_write_permissions(self, add_write: bool):
        """
        Method to find manage permission ACL and add/remove write permission.
        :param add_write: If True find MANAGE_PERMISSION_LOCK and change to MANAGE_PERMISSION_UNLOCK; if False visa versa
        :type add_write: Bool
        """
        new_entries = []
        target = self.MANAGE_PERMISSION_LOCK if add_write else self.MANAGE_PERMISSION_UNLOCK
        replacement = self.MANAGE_PERMISSION_UNLOCK if add_write else self.MANAGE_PERMISSION_LOCK
        for entry in self.permissions.entries:
            permission = entry.permissions
            if sorted(list(permission)) == sorted(list(target)):
                permission = replacement
                entry.permissions = permission
            new_entries.append(entry)
        self.permissions = AccessControlList(new_entries)

    def _subdirectories(self):
        """
        Generator for all subdirectories in a share
        """
        for o in os.listdir(self.directory):
            if os.path.isdir(os.path.join(self.directory, o)):
                yield os.path.join(self.directory, o)

    def _makedir(self, directory):
        """
        Created a directory and outputs to log
        """
        logging.debug("Creating %s" % directory)
        os.makedirs(directory)
        self.permissions.set(target=directory)

    def _link_files(self, source, target, shared_item_list=[]):
        """
        Creates a hard link between two files and outputs to log
        """
        try:
            logging.debug("Linking %s and %s" % (source, target))
            os.link(os.path.realpath(source), target)
        except PermissionError as e:
            msg = "ERROR: Insufficient rights on {}! " \
                  "Possible cause; source file need to be writable/appendable when fs.protect_hardlinks is enabled. " \
                  "Permissions: {}"
            logging.error(msg.format(e.filename, str(AccessControlList.from_file(source))))
            shared_item_list.remove(e.filename)
        except FileExistsError as e:
            logging.debug("File %s already exists!" % e.filename)    
            shared_item_list.remove(e.filename)
        return shared_item_list

    def self_destruct(self, force_file_removal=False):
        """
        will have the share remove itself
        """
        self._unshare_linked_tree(directory=self.directory, force_file_removal=force_file_removal)
    
    def remove_items(self, items, force_file_removal=False):
        """
        Remove items from share
        """
        for item in items:
            self._unshare_file(item, force=force_file_removal)

    @staticmethod
    def _unshare_dir(target):
        """
        Removes a directory from this share, fails when directory is not empty
        """
        logging.debug("Un-sharing directory %s" % target)
        os.rmdir(target)

    @staticmethod
    def _unshare_file(target, force=False):
        """
        Removes a file from this share
        """
        logging.debug("Un-sharing file %s" % target)
        if not force and os.stat(target).st_nlink == 1:
            msg = "File %s has ONE hard link. Un-sharing this file will delete it! Apply \'--force\' to do so." % target
            logging.error(msg)
            raise FileNotFoundError(msg)
        os.unlink(target)


class IllegalShareSetupError(RuntimeError):
    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


LOCK_ACE = AccessControlEntity(entry_type="D",
                               flags="",
                               identity="EVERYONE",
                               domain='',
                               permissions="wadDNTo")
LOCK_ACL = AccessControlList([LOCK_ACE])
