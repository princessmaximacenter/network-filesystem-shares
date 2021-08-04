#! /usr/bin/env python

import argparse
import logging
import sys
import subprocess
from . import manage
from . import acl


def _cli_argument_parser():
    """
    Parses the command-line interface arguments and does basic checks on validity.
    """
    global parser
    parser = argparse.ArgumentParser(
        prog="share",
        description="Shares only work when items and share are on the same filesystem that supports NFSv4 ACL.")

    default_domain = acl.get_nfs4_domain()

    default_args = {
        "share_directory": (
            ["share_directory"],
            {'metavar': "SHARE_DIRECTORY", 'help': "The path to the directory representing the share"}
        ),
        "items": (
            ["-i", "--item", "--items"],
            {"nargs": "*", "metavar": "ITEM", "action": "extend", "default": [],
             "help": "one or paths of files or directories to share", "dest": 'items'}
        ),
    }
    parser.add_argument("-v", "--verbose", action="count", default=0,
                        help="increases output verbosity (DEBUG is \'-vv\')", dest="verbosity")
    subparsers = parser.add_subparsers(title='subcommands',
                                       description='valid subcommands')
    # Sub-parser for creating a share
    create_parser = subparsers.add_parser('create', aliases=['new'],
                                          help='creates a share directory (help: \'create -h\')')
    # Following enables the use of extend action; so when doing "prog -i a b -i c" gives [a, b, c] instead of [[a,b], c]
    create_parser.register('action', 'extend', ExtendAction)
    create_parser.set_defaults(func=manage.create)
    for arg in default_args:  # Add the default args (share and item)
        create_parser.add_argument(*default_args[arg][0], **default_args[arg][1])
    create_parser.add_argument('-u', '--user', '--users', action='extend', nargs="*", required=False, metavar='USER',
                               dest='users',
                               help='give access to user (can be defined multiple times)')
    create_parser.add_argument('-g', '--group', '--groups', action='extend', nargs="*", required=False, metavar='GROUP',
                               dest='groups',
                               help='give access to group (can be defined multiple times)')
    create_parser.add_argument('-mu', '--managing_user', '--managing_users', action='extend', nargs="*", required=False,
                               metavar='USER',
                               dest='managing_users',
                               help='give permission to user to manage share (can be defined multiple times)')
    create_parser.add_argument('-mg', '--managing_group', '--managing_groups', action='extend', nargs="*",
                               required=False,
                               metavar='GROUP', dest='managing_groups',
                               help='give permission to group to manage share (can be defined multiple times)')
    create_parser.add_argument('-d', '--domain', required=False, dest='domain', default=default_domain,
                               help="general domain used to build the user and group principles (NFSv4 ACLs) "
                                    "if not provided it is looked up using command dnsdomainname")
    create_parser.add_argument('-saa', '--service-application-accounts ', action='extend', nargs="*", required=False, dest='service_application_accounts',
                               help="service application accounts under which the services (e.g. HTTP) are running that should have access to the share (NFSv4 ACLs)")
    create_parser.add_argument('-uad', '--user-apache-directive', required=False,
                               default="Require ldap-user {}",
                               help="This directive template specifies an user who is allowed access "
                                    "to a share via htaccess. "
                                    "Default: 'Require ldap-user {}' where {} is replaced by the user")
    create_parser.add_argument('-gad', '--group-apache-directive', required=False,
                               default="Require ldap-group cn={},cn=groups,cn=accounts,dc=researchidt,dc=prinsesmaximacentrum,dc=nl",
                               help="This directive template specifies an group whose members are allowed access "
                                    "to a share via htaccess. "
                                    "Default: 'Require ldap-group cn={},cn=groups,cn=accounts,dc=researchidt,dc=prinsesmaximacentrum,dc=nl' where {} is replaced by the group")

    # Sub-parser for removing a share
    delete_parser = subparsers.add_parser('delete', aliases=['rm', 'remove', 'del'],
                                          help='deletes a share directory (help: \'delete -h\')')
    delete_parser.set_defaults(func=manage.delete)
    for args in ['share_directory']:
        delete_parser.add_argument(*default_args[args][0], **default_args[args][1])
    delete_parser.add_argument('-f', '--force', action="store_true", default=False,
                               help="forces files to be un-shared even if they have only one hard link (i.e. delete "
                                    "files)")

    # Sub-parser for adding things to a share
    add_parser = subparsers.add_parser('add',
                                       help='adds items, users or groups a share directory (help: \'add -h\')')
    add_parser.set_defaults(func=manage.add)
    add_parser.register('action', 'extend', ExtendAction)
    for args in ['share_directory', 'items']:
        add_parser.add_argument(*default_args[args][0], **default_args[args][1])
    add_parser.add_argument('-u', '--user', '--users', action='extend', nargs="*", required=False, metavar='USER',
                            dest='users',
                            help='give access to user (can be defined multiple times)')
    add_parser.add_argument('-g', '--group', '--groups', action='extend', nargs="*", required=False, metavar='GROUP',
                            dest='groups',
                            help='give access to group (can be defined multiple times)')
    add_parser.add_argument('-mu', '--managing_user', '--managing_users', action='extend', nargs="*", required=False,
                            metavar='USER',
                            dest='managing_users',
                            help='give permission to user to manage share (can be defined multiple times)')
    add_parser.add_argument('-mg', '--managing_group', '--managing_groups', action='extend', nargs="*", required=False,
                            metavar='GROUP',
                            dest='managing_groups',
                            help='give permission to group to manage share (can be defined multiple times)')
    add_parser.add_argument('-d', '--domain', required=False, dest='domain', default=default_domain,
                            help="general domain used to build the user and group principles (NFSv4 ACLs)"
                                 "if not provided it is looked up using command dnsdomainname")
    add_parser.add_argument('-saa', '--service-application-accounts ', action='extend', nargs="*", required=False, dest='service_application_accounts',
                            help="service application accounts under which the services (e.g. HTTP) are running that should have access to the share (NFSv4 ACLs)")
    return parser


class ExtendAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest) or []
        items.extend(values)
        setattr(namespace, self.dest, items)


def main(parser):
    """
    Main entry point when using this module via the command-line interface
    """
    args = parser.parse_args()

    # Get the dictionary from input arguments
    args_dict = vars(args)

    if 'func' not in args_dict:
        parser.print_help()
        sys.exit(1)

    # Set-Up logging
    log_level = logging.ERROR

    if args.verbosity == 1:
        log_level = logging.INFO
    elif args.verbosity >= 2:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level, format='%(module)s:\t%(levelname)s\t%(message)s')

    logging.debug("Command-line call (parsed): %s" % " ".join(sys.argv[:]))
    logging.debug("Parsed args: %s" % args_dict)

    # Unpack the dictionary to the selected function (e.g. 'create', 'remove' (excluding the 'func' key)
    share = args.func(**{x: args_dict[x] for x in args_dict if x not in ['func', 'verbosity']})

    if args.func.__name__ != 'delete':
        logging.info("Filesystem path to share is: %s" % share.directory)
        data_dir = '/data/groups/pmc_omics_test'
        fqdn_url = 'https://files.bioinf.prinsesmaximacentrum.nl'
        if share.directory.count(data_dir) > 0:
            logging.info("URL to share: %s" % share.directory.replace(data_dir, fqdn_url))
        else:
            logging.warning("Could not generate URL (\'%s\' not in \'%s\')" % (data_dir, share.directory))


def entry_point():
    main(_cli_argument_parser())
