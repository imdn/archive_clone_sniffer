# -*- coding: utf-8 -*-
"""
@author: imad
"""

from archiveclonesniffer import *
from terminaltables import AsciiTable, SingleTable
import argparse
import sys
import os

MAX_TABLE_WIDTH = 0;
LINE_CHAR = u'\u2500' #'─'

######################################################################
# To overcome the nasty Unicode - chcp 65001 bug on Windows !@$@#$
# Bug prevents unicode characters from displaying on stdout or
# redirecting output to files throwing a UnicodeEncodeError exception
# Credits - http://stackoverflow.com/a/1432462/979234
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


class CmdProcessor:
    def __init__(self):
        parser = argparse.ArgumentParser(description='Manage ZIP/RAR archive files in an Sqlite3 Database')
        parser.add_argument ('-db', '--database', help="Name of Sqlite-3 database to use/create")

        parser.add_argument('-f',   '--files', nargs = '+',   help = "List of files to compare against archive or database")
        parser.add_argument('-a',   '--archive', help = 'Archive to add, or to compare against another archive or database')
        parser.add_argument('-a2',  '--archive2', help = 'Archive to compare an archive against')
        parser.add_argument('--force', help = 'Force addition of archive to database even if there are matching files', action="store_true")

        operations_group = parser.add_mutually_exclusive_group()
        operations_group.add_argument ('--add', help="Add archive to database. 0-byte files and directories are not added", action="store_true")
        operations_group.add_argument ('--create', help = "Create database", action="store_true")
        operations_group.add_argument ('--reset',  help = "Reinitialize existing database", action="store_true")
        operations_group.add_argument ('--compare', help = "Perform comparisions. Priority (1) Archive vs. DB (2) List of files vs. DB (3) Archive vs. Archive (4) List of files vs. Archive", action="store_true", default=True)
        operations_group.add_argument ('--sql', help = "Run SQL query on database")
        operations_group.add_argument ('--delete', help="Delete entries for 'archive' in the database", action="store_true")

        parser.set_defaults(add=False, create=False, reset=False, compare=False, force=False, delete=False)

        self.args = parser.parse_args()
        if len(sys.argv) == 1:
            print parser.format_usage()

def print_banner(width, heading=None, char=None):
    if char is None:
        # u2550 - ══
        # u2500 - ──
        char =  LINE_CHAR
    if heading is not None:
        padded_heading = ' ' + heading + ' '
        half_width = (width - len(padded_heading))/2
        banner = char * half_width + padded_heading + char*half_width
        if len(banner) < width:
            banner = banner + char
    else:
        banner = char * width
    print banner

def report(data, table_heading=None, description=None, banner=False):
    global MAX_TABLE_WIDTH
    table_data = data
    table = SingleTable(table_data, table_heading)
    if MAX_TABLE_WIDTH < table.table_width:
        MAX_TABLE_WIDTH = table.table_width
    print
    if banner:
        print_banner(table.table_width, 'REPORT')
        print
    if description:
        print description
    if (len(data) > 1):
        if table_heading:
            print
        print table.table

def show_full_report(matched_files, archive_stats, unmatched_stats):
    global MAX_TABLE_WIDTH
    if len(matched_files) > 1:
        report(matched_files,  'Matching Files', "{} matching file(s) found".format(len(matched_files)-1), banner=True)
        if len(archive_stats) > 1:
            report(archive_stats, 'Archives', "{} archive(s) contain the matched files".format(len(archive_stats)-1))
        report(unmatched_stats, description='{} unmatched file(s)'.format(len(unmatched_stats) -1))
    else:
        MAX_TABLE_WIDTH = 60
        print
        print_banner(MAX_TABLE_WIDTH, 'REPORT')
        print
        print "No matching files found in the current comparison"
        print
    print_banner(MAX_TABLE_WIDTH, char=LINE_CHAR)


def do_comparison(database, files, archive, archive2):
    try:
        if database is not None:
            db = Database(database)
            if archive is not None:
                # compare db vs archive
                print
                print_banner(100, "Comparing: {} vs. {}".format(database, archive), LINE_CHAR)
                comparator = Comparator(database=db, archive=archive)
                file_match, archive_match, non_match = comparator.compareArchivexDatabase()
            elif files is not None:
                # compare db vs files
                print
                print_banner(100, "Comparing: {} vs. {}".format(database, '<file(s)>'), LINE_CHAR)
                comparator = Comparator(database=db, files=files)
                file_match, archive_match, non_match = comparator.compareFilexDatabase()
                print "Finish comparison"
            db.close()
        elif archive is not None:
            if archive2 is not None:
                # compare two archives
                print
                print_banner(100, "Comparing: {} vs. {}".format(archive, archive2), LINE_CHAR)
                comparator = Comparator(archive=archive, reference_archive=archive2)
                file_match, archive_match, non_match = comparator.compareArchivexArchive()
            elif files is not None:
                # compare archive against files
                print
                print_banner(100, "Comparing: {} vs. {}".format(archive, '<file(s)>'), LINE_CHAR)
                comparator = Comparator(archive=archive, files=files)
                file_match, archive_match, non_match = comparator.compareFilexArchive()
        else:
            print
            print "ERROR! Must compare {DB vs. Archive} OR {DB vs. Files} OR {Archive vs. Archive} OR {Archive vs. Files}"
            return

        show_full_report(file_match, archive_match, non_match)

    except sqlite3.Error as e:
        print "ERROR! Could not compare with database. Sqlite3 said: \"{}\"".format(e.message)
        db.close()
    except WindowsError as e:
        print "ERROR! Err. Message : \"{}\"".format(e)
        sys.exit(-1)



def assert_argument_present(param, required_param, argument=None):
    if param is None:
        print "ERROR! '{}' argument must be supplied for '{}'".format(required_param,argument)
        sys.exit(0)

def add_archive_to_db(archive, database, force_add=False):
    assert_argument_present(database, "-db/--database", "-add");
    assert_argument_present(archive, "-a/--archive", "-add");
    try:
        db = Database(database)
        arc = Archive(archive)
        comparator = Comparator(archive=archive, database=db)
        file_match, archive_match, non_match = comparator.compareArchivexDatabase()
        if len(file_match) > 1:
            show_full_report(file_match, archive_match, non_match)
            print
            if not force_add:
                print "WARNING! Will not add '{}' to database - '{}' until duplicate files are removed".format(archive, db.name)
                db.close()
                return
            else:
                print "WARNING! '{}' contains duplicate files but will be added to database '{}' anyways".format(archive, db.name)
        print
        print "Now adding '{}' to database ...".format(archive)
        db.addArchivetoDB(arc)
        print "Done"
        db.close()

    except sqlite3.IntegrityError as e:
        print "ERROR! Could not write to database. Sqlite3 said: \"{}\"".format(e.message)
        db.close()
    except sqlite3.Error as e:
        print "ERROR! Could not write to database. Sqlite3 said: \"{}\"".format(e.message)
        db.close()

def reset_db(database):
    assert_argument_present(database, "-db/--database", "-r/-reset")
    try:
        print "Resetting database '{}' ...".format(database)
        db = Database(database)
        db.resetDB()
        db.close()
        print "Done"
    except sqlite3.Error as e:
        print "ERROR! Could not reset database. Sqlite3 said: \"{}\"".format(e.message)
        db.close()


def create_db(database):
    assert_argument_present(database, "-db/--database", "-c/--create")
    try:
        print "Now creating database  '{}' ...".format(database)
        db = Database(database)
        db.initDB()
        db.close()
        print "Done"
    except sqlite3.Error as e:
        print "ERROR! Could not create database. Sqlite3 said: \"{}\"".format(e.message)
        db.close()

def run_sql_query(database, sql):
    assert_argument_present(database, "-db/--database", "-s/--sql")
    try:
        db = Database(database)
        header, records = db.runSQL(sql)
        rows = map(list, records) # Convert tuple of tuples to list of lists
        data = [header]
        data.extend(rows)
        table = SingleTable([map(str,row) for row in data]) # Convert all items in inner-list of lists to strings
        #table.inner_heading_row_border = False
        print table.table
        print "{} row(s) affected".format(len(rows))
        db.close()

    except sqlite3.Error as e:
        print "ERROR! Could not run query. Sqlite3 said : \"{}\"".format(e.message)
        db.close()


def delete_archive_from_db(database, archive):
    assert_argument_present(database, "-db/--database", "-d/--delete")
    assert_argument_present(database, "-a/--archive", "-d/--delete")
    try:
        db = Database(database)
        header, records = db.deleteArchive(archive)
        if header is None and len(records) == 0:
            print "No entry for '{}' found in database '{}'".format(archive, database)
        elif len(records) > 1:
            print "\nMore than one matching archive found. Not deleted"
            rows = map(list, records) # Convert tuple of tuples to list of lists
            data = [header]
            data.extend(rows)
            table = SingleTable([map(str,row) for row in data]) # Convert all items in inner-list of lists to strings
            #table.inner_heading_row_border = False
            print table.table
            print "\nUse SQL statement - DELETE FROM archive_name WHERE archive_sha1 LIKE '<checksum>' instead"
        else:
            print "{} deleted successfully from database '{}'".format(archive, database)
        db.close()

    except sqlite3.Error as e:
        print "ERROR! Could not delete archive from database. Sqlite3 said : \"{}\"".format(e.message)
        db.close()

def init():
    c = CmdProcessor()
    args = c.args

    database = args.database
    files = args.files
    archive = args.archive
    archive2 = args.archive2

    if args.compare:
        # Comparison
        do_comparison(database, files, archive, archive2)
        return

    if args.add:
        add_archive_to_db(archive, database, args.force)
        return

    if args.create:
        create_db(database)
        return

    if args.reset:
        reset_db(database)
        return

    if args.sql:
        run_sql_query(database, args.sql)
        return

    if args.delete:
        delete_archive_from_db(database, archive)
        return

init()