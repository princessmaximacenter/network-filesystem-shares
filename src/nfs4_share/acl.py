import os
import re
import pwd
import grp
import subprocess
import logging

# Basic paths to binaries
getfacl_bin = "/usr/bin/nfs4_getfacl"
setfacl_bin = "/usr/bin/nfs4_setfacl"


def assert_command_exists(command_path):
    assert os.path.isfile(command_path) and os.access(command_path, os.X_OK), "Reading the nfs4 access-control list " \
                                                                              "requires the executable binary '%s'" % \
                                                                              command_path


class AccessControlList:
    """
    Representation of an NFSv4 ACL (LIST)
    """

    def __init__(self, entries):
        if type(entries) not in [set, list]:
            raise TypeError("Entries should be a set or list")
        self.entries = entries

    def __repr__(self):
        return ",".join([repr(i) for i in self.entries])

    def __eq__(self, other):
        return self.entries == other.entries

    def __iter__(self):
        return iter(self.entries)

    def __sub__(self, other):  # self - other
        first_index, last_index = find_sub_list(other.entries, self.entries)
        if first_index is None:  # No sublist was found
            return self
        new_acl = AccessControlList(self.entries[:first_index]+self.entries[last_index+1:])
        return new_acl

    def __add__(self, other):
        new_acl = AccessControlList(self.entries + other.entries)
        return new_acl

    @classmethod
    def from_file(cls, filename):
        """Calls the nfs4_getfacl binaries via CLI to get ACEs"""
        global getfacl_bin
        assert_command_exists(getfacl_bin)
        try:
            output = subprocess.check_output([getfacl_bin, filename], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            logging.error(e.cmd)
            logging.error(e.stdout.decode())
            logging.error(e.stderr.decode())
            raise e
        entries = []
        for line in nonblank_lines(output.decode().split("\n")):
            if line.startswith('#'):
                continue
            entry = AccessControlEntity.from_string(line, filename=filename)
            entries.append(entry)
        if len(entries) == 0:
            raise OSError("Could not get ACLs from file \'%s\'" % filename)
        return cls(entries)

    def append(self, *args, **kwargs):
        self._change_nfs4('-a', *args, **kwargs)

    def set(self, *args, **kwargs):
        self._change_nfs4('-s', *args, **kwargs)

    def unset(self, *args, **kwargs):
        self._change_nfs4('-x', *args, **kwargs)

    def _change_nfs4(self, action, target, recursive=False, test=False):
        """
        Calls the nfs4_setfacl binaries via CLI to change permissions
        """
        logging.debug("Changing permissions (%s) on %s (recursive=%s)" % (action, target, recursive))
        global setfacl_bin
        assert_command_exists(setfacl_bin)
        command = [setfacl_bin]
        if recursive:
            command.append('-R')
        if test:
            command.append('--test')
        command.append(action)
        command.extend([repr(self), target])
        try:
            subprocess.check_output(command, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            logging.error("Subprocess: %s" % e.cmd)
            logging.error("Subprocess: %s" % e.output.decode())
            raise e


class AccessControlEntity:
    """
    Representation of an NFSv4 ACE (Entity)
    """
    ace_spec = "{entry_type}:{flags}:{identity}@{domain}:{permissions}"

    def __init__(self, entry_type, flags, identity, domain, permissions):
        self.entry_type = entry_type
        self.flags = flags
        self.identity = identity
        self.domain = domain
        self.permissions = permissions

    def __repr__(self):
        return self.ace_spec.format(
            entry_type=self.entry_type,
            flags=self.flags,
            identity=self.identity,
            domain=self.domain,
            permissions=self.permissions)

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        if self.entry_type != other.entry_type \
                or self.flags != other.flags \
                or self.domain != other.domain \
                or self.identity != other.identity:
            return False
        if len(self.permissions) != len(other.permissions):
            return False
        for perm in self.permissions:
            if perm not in other.permissions:
                return False
        return True

    @property
    def permissions(self):
        return self._permissions

    @permissions.setter
    def permissions(self, value):
        for letter in value:
            if letter in ['R', 'W', 'X']:
                raise NotImplementedError("Upper-case permissions are not allowed (%s) [R->rtncy, W->waDtTNcCy, "
                                          "X->xtcy]" % value)
        self._permissions = value

    @classmethod
    def from_string(cls, string, filename=None):
        """
            Returns a AccessControlEntity tat is based on a string.
            A filename is required if one wants to translate special principal
        """
        components = string.split(':')
        entry_type = components[0]
        flags = components[1]
        principal = components[2]
        if principal in ['OWNER@', 'GROUP@', 'EVERYONE@']:
            assert filename is not None, "filename is required to make a special principal translation!"
            identity, domain, flags = cls.translate_special_principals(principal, filename, flags)
        else:
            split = principal.split('@')
            identity = split[0]
            domain = split[1]
        permissions = components[3]
        return cls(entry_type, flags, identity, domain, permissions)

    @staticmethod
    def translate_special_principals(principal, filename, flags):
        """
        Translates a special principal to the actual user / group name. NFS4 share domain is taken from /etc/idmapd.conf and falls back on `dnsdomainname`.
        Returns identity, domain and flags"""
        domain = get_nfs4_domain()
        stat_info = os.stat(filename)
        if 'OWNER@' == principal:
            uid = stat_info.st_uid
            user = pwd.getpwuid(uid)[0]
            return user, domain, flags
        elif 'GROUP@' == principal:
            gid = stat_info.st_gid
            group = grp.getgrgid(gid)[0]
            flags = flags+'g'
            return group, domain, flags
        elif 'EVERYONE@' == principal:
            return "EVERYONE", '', flags
        else:
            raise NotImplementedError("Cannot translate %s" % principal)


def get_nfs4_domain():
    domain = subprocess.run(['egrep', '-s', '^Domain', '/etc/idmapd.conf'], stdout=subprocess.PIPE).stdout.decode('utf-8').rstrip()
    try:
        domain = re.search('[a-z\\.\\-]+$', domain).group(0)
    except AttributeError:
        pass
    if len(domain) == 0:
        domain = subprocess.run(['dnsdomainname'], stdout=subprocess.PIPE).stdout.decode('utf-8').rstrip()
    return (domain)


def nonblank_lines(f):
    for line in f:
        line = line.rstrip()
        if line:
            yield line


def find_sub_list(sublist, mainlist):
    sublist_length = len(sublist)
    for index in (i for i, e in enumerate(mainlist) if e == sublist[0]):
        if mainlist[index:index + sublist_length] == sublist:
            return index, index+sublist_length-1
    return None, None
