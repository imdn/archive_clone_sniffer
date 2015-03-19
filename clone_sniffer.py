# -*- coding: utf-8 -*-
"""
@author: imad
"""

from archiveclonesniffer import *
from terminaltables import AsciiTable, SingleTable
import archiveclonesniffer.presenter as P
import argparse
import sys
import os

MAX_TABLE_WIDTH = 0;
LINE_CHAR = '\u2500' # Box drawing character '─'

########################## For Python 2.x #################################
###################### WARNING! Doesn't always work #######################
if sys.version_info < (3,0):
    ######################################################################
    # UNICODE FIX - NOT NEEDED FOR PYTHON 3
    # To overcome the nasty Unicode bug on Windows !@$@#$
    # Bug prevents unicode characters from displaying on stdout or
    # redirecting output to files throwing a UnicodeEncodeError exception
    # Even chcp 65001 does not work as expected with Python 2.x
    # Credits for snippet below- http://stackoverflow.com/a/1432462/979234
    ######################################################################
    if sys.platform == "win32":
        class UniStream(object):
            __slots__= ("fileno", "softspace",)

            def __init__(self, fileobject):
                self.fileno = fileobject.fileno()
                self.softspace = False

            def write(self, text):
                os.write(self.fileno, text.encode("utf_8") if isinstance(text, unicode) else text)

        sys.stdout = UniStream(sys.stdout)
        sys.stderr = UniStream(sys.stderr)
        ######################################################################
    LINE_CHAR = u'\u2500' #'─'
    warning_str1 = "WARNING! You are running Python {}.{}.{}".format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro)
    warning_str2 = "In case unicode problems arise or you see garbled characters, try switching to Python 3.3"
    print(LINE_CHAR * len(warning_str2))
    print(warning_str1 + "\n" + warning_str2)
    print(LINE_CHAR * len(warning_str2))
##############################################################################

class CmdProcessor:
    def __init__(self):
        parser = argparse.ArgumentParser(
            description='Manage Sqlite3 Database catalog of ZIP/RAR archive file contents.'
            #epilog = 'Priority of operations in case more than one is provided: Compare > List > Schema > Backup > Add > Create > Reset > SQL > Delete'
        )
        parser.add_argument ('-db', '--database', help="Name of Sqlite-3 database to use/create")

        parser.add_argument('-f',   '--files', nargs = '+',   help = "List of files to compare against archive or database")
        parser.add_argument('-a',   '--archive', help = 'Archive to add, or to compare against another archive or database')
        parser.add_argument('-a2',  '--archive2', help = 'Archive to compare an archive against')
        parser.add_argument('--force', help = 'Force addition of archive to database even if there are matching files', action="store_true")

        operations_group = parser.add_mutually_exclusive_group()
        operations_group.add_argument ('--compare', help = "Perform comparisions. Priority (1) Archive vs. DB (2) List of files vs. DB (3) Archive vs. Archive (4) List of files vs. Archive", action="store_true", default=True)
        operations_group.add_argument ('--list', help="List files for the given 'archive' in the database", action="store_true")
        operations_group.add_argument ('--schema', help="Show database schema", action="store_true")
        operations_group.add_argument ('--backup', help="Backup database", action="store_true")
        operations_group.add_argument ('--add', help="Add archive to database. 0-byte files and directories are not added", action="store_true")
        operations_group.add_argument ('--create', help = "Create database", action="store_true")
        operations_group.add_argument ('--reset',  help = "Reinitialize existing database", action="store_true")
        operations_group.add_argument ('--sql', help = "Run given SQL query on database")
        operations_group.add_argument ('--delete', help="Delete entries for given 'archive' in the database", action="store_true")

        parser.set_defaults(add=False, create=False, reset=False, compare=False, force=False, delete=False)

        self.args = parser.parse_args()
        if len(sys.argv) == 1:
            print(parser.format_usage())

def assert_argument_present(param, required_param, argument=None):
    if param is None:
        print("ERROR! '{}' argument must be supplied for '{}'".format(required_param,argument))
        sys.exit(0)

def init():
    c = CmdProcessor()
    args = c.args

    database = args.database
    files = args.files
    archive = args.archive
    archive2 = args.archive2
    result = ""

    if args.compare:
        # Comparison
        result = P.do_comparison(database, files, archive, archive2)
    elif args.list:
        assert_argument_present(archive, "-a/--archive", "--list")
        database = '' if (database is None) else database
        result = P.list_archive_contents(archive, database)
    elif args.schema:
        assert_argument_present(database, "-d/--database", "--schema")
        result = P.get_database_schema(database)
    elif args.backup:
        assert_argument_present(database, "-d/--database", "--backup")
        result = P.backup_database(database)
    elif args.add:
        assert_argument_present(database, "-db/--database", "-add");
        assert_argument_present(archive, "-a/--archive", "-add");
        result = P.add_archive_to_db(archive, database, args.force)
    elif args.create:
        assert_argument_present(database, "-db/--database", "-c/--create")
        result = P.create_db(database)
    elif args.reset:
        assert_argument_present(database, "-db/--database", "-r/-reset")
        result = P.reset_db(database)
    elif args.sql:
        assert_argument_present(database, "-db/--database", "-s/--sql")
        result = P.run_sql_query(database, args.sql)
    elif args.delete:
        assert_argument_present(database, "-db/--database", "-d/--delete")
        assert_argument_present(database, "-a/--archive", "-d/--delete")
        result = P.delete_archive_from_db(database, archive)

    print(result)

init()
