# -*- coding: utf-8 -*-
"""
@author: imad
"""

import sys
import os
import time
import shutil
from archiveclonesniffer import *
from terminaltables import AsciiTable, SingleTable

LINE_CHAR = '\u2500'
MAX_TABLE_WIDTH = 100

def create_banner(width, heading=None, char=None):
	if char is None:
		# u2550 - ══
		# u2500 - ──
		char =  LINE_CHAR
	if heading is not None:
		padded_heading = ' ' + heading + ' '
		half_width = int((width - len(padded_heading))/2)
		banner = char*half_width + padded_heading + char*half_width
		if len(banner) < width:
			banner = banner + char
	else:
		banner = char * width
	return banner

def create_report(data, table_heading=None, description=None, banner=False):
	global MAX_TABLE_WIDTH
	output_str = ""
	table_data = data
	table = SingleTable(table_data, table_heading)
	if MAX_TABLE_WIDTH < table.table_width:
		MAX_TABLE_WIDTH = table.table_width
	output_str += "\n"
	if banner:
		output_str += create_banner(table.table_width, 'REPORT')
		output_str += "\n"
	if description:
		output_str += description
	if (len(data) > 1):
		if table_heading:
			output_str += "\n"
		output_str += table.table
	return output_str

def show_full_report(matched_files, archive_stats, unmatched_stats):
	global MAX_TABLE_WIDTH
	output_str = ""
	if len(matched_files) > 1:
		output_str += create_report(matched_files,  'Matching Files', "{} matching file(s) found\n".format(len(matched_files)-1), banner=True)
		if len(archive_stats) > 1:
			output_str += create_report(archive_stats, 'Archives', "\n{} archive(s) contain the matched files".format(len(archive_stats)-1))
		output_str += create_report(unmatched_stats, description='\n{} unmatched file(s) in archive\n'.format(len(unmatched_stats) -1))
	else:
		#MAX_TABLE_WIDTH = 60
		output_str += "\n"
		output_str += create_banner(MAX_TABLE_WIDTH, 'REPORT')
		output_str += "\n"
		output_str += "No matching files found in the current comparison"
		output_str += "\n"
	output_str += "\n"
	output_str += create_banner(MAX_TABLE_WIDTH, char=LINE_CHAR)
	return output_str

def assert_argument_present(param, required_param, argument=None):
	if param is None or param == '':
		return "ERROR! '{}' argument must be supplied for '{}'".format(required_param,argument)
		#sys.exit(0)

def do_comparison(database, files, archive, archive2):
	output_str = ""
	try:
		if database is not None:
			db = Database(database)
			if archive is not None:
				# compare db vs archive
				output_str += "\n"
				output_str += create_banner(100, "Comparing: {} vs. {}".format(os.path.basename(database), os.path.basename(archive)), LINE_CHAR)
				comparator = Comparator(database=db, archive=archive)
				output_str += "\nFinished comparison"
				file_match, archive_match, non_match = comparator.compareArchivexDatabase()
			elif files is not None:
				# compare db vs files
				output_str += "\n"
				output_str += create_banner(100, "Comparing: {} vs. {}".format(os.path.basename(database), '<file(s)>'), LINE_CHAR)
				comparator = Comparator(database=db, files=files)
				file_match, archive_match, non_match = comparator.compareFilexDatabase()
				output_str += "Finished comparison"
			db.close()
		elif archive is not None:
			if archive2 is not None:
				# compare two archives
				output_str += "\n"
				output_str += create_banner(100, "Comparing: {} vs. {}".format(os.path.basename(archive), os.path.basename(archive2)), LINE_CHAR)
				comparator = Comparator(archive=archive, reference_archive=archive2)
				file_match, archive_match, non_match = comparator.compareArchivexArchive()
			elif files is not None:
				# compare archive against files
				output_str += "\n"
				output_str += create_banner(100, "Comparing: {} vs. {}".format(os.path.basename(archive), '<file(s)>'), LINE_CHAR)
				comparator = Comparator(archive=archive, files=files)
				file_match, archive_match, non_match = comparator.compareFilexArchive()
		else:
			output_str += "\nERROR! Must compare {DB vs. Archive} OR {DB vs. Files} OR {Archive vs. Archive} OR {Archive vs. Files}"
			return output_str

		output_str += "\n" + show_full_report(file_match, archive_match, non_match)
		return output_str

	except sqlite3.Error as e:
		db.close()
		output_str += "\nERROR! Could not compare with database.\n\nSqlite3 said: \"{}\"".format(e)
		return output_str
	except WindowsError as e:
		output_str += "\nERROR! Err. Message : \"{}\"".format(e)
		return output_str

def list_archive_contents(archive, database):
	archive_only = False
	archive_basename  = os.path.basename(archive)
	database_basename = os.path.basename(database)
	output_str = ""

	if database is None or database == '':
		archive_only = True
	try:
		if archive_only:
			arc = Archive(archive)
			empty_msg = "Archive '{}' seems to be empty".format(archive_basename)
			header, records = arc.listArchiveContents()
		else:
			db = Database(database)
			empty_msg = "Database '{}' does not contain any records for archive '{}'".format(database_basename, archive_basename)
			#empty_msg = "Database '{}' does not contain any records for archive '{}'".format(database_basename, archive)
			header, records = db.listArchiveContents(archive_basename)
			db.close()
		if len(records) > 0:
			rows = list(map(list, records)) # Convert tuple of tuples to list of lists
			data = [header]
			data.extend(rows)
			#print("{}".format(data))
			table = SingleTable([list(map(str,row)) for row in data]) # Convert all items in inner-list of lists to strings
			#table.inner_heading_row_border = False
			table_str = table.table
			output_str += create_banner(table.table_width, "Listing contents of '{}'".format(archive_basename))
			output_str += "\n" + table_str
			output_str += "\n{} file(s) in archive '{}'".format(len(rows), archive_basename)
			if archive_only:
				output_str += "\n\nArchive SHA-1 checksum - {}".format(arc.sha1)
		else:
			#banner = "\n" + create_banner(MAX_TABLE_WIDTH, 'REPORT') + "\n"
			output_str += empty_msg
		return output_str

	except sqlite3.Error as e:
		db.close()
		exceptMsg = "ERROR! Could not list archive.\n\nSqlite3 said: \"{}\"".format(e)
		return exceptMsg
	except WindowsError as e:
		exceptMsg = "ERROR! Err. Message : \"{}\"".format(e)
		return exceptMsg
		#sys.exit(-1)

def add_archive_to_db(archive, database, force_add=False):
	assert_argument_present(database, "-db/--database", "-add")
	assert_argument_present(archive, "-a/--archive", "-add")
	output_str = ""
	try:
		db = Database(database)
		arc = Archive(archive)
		comparator = Comparator(archive=archive, database=db)
		file_match, archive_match, non_match = comparator.compareArchivexDatabase()
		if len(file_match) > 1:
			show_full_report(file_match, archive_match, non_match)
			output_str += "\n"
			if not force_add:
				output_str += "WARNING! Will not add '{}' to database - '{}'.\nRemove duplicate files first".format(archive, db.name)
				db.close()
				return output_str
			else:
				output_str += "WARNING! '{}' contains duplicate files but will be added to database '{}' anyways".format(archive, db.name)
		output_str += "\n"
		output_str += "Adding '{}' to database ... ".format(archive)
		db.addArchivetoDB(arc)
		output_str += "Done.\n  \n{} files (excl. 0-byte files) from '{}' added".format(arc.total_files, os.path.basename(archive))
		db.close()
		return output_str

	except sqlite3.IntegrityError as e:
		db.close()
		exceptMsg = "ERROR! Could not write to database. Sqlite3 said: \"{}\"".format(e)
		return exceptMsg
	except sqlite3.Error as e:
		db.close()
		exceptMsg = "ERROR! Could not write to database. Sqlite3 said: \"{}\"".format(e)
		return exceptMsg

def delete_archive_from_db(archive, database):
    assert_argument_present(database, "-db/--database", "-d/--delete")
    assert_argument_present(database, "-a/--archive", "-d/--delete")
    output_str = ""
    try:
        db = Database(database)
        header, records = db.deleteArchive(archive)
        if header is None and len(records) == 0:
            output_str += "No entry for '{}' found in database '{}'".format(archive, database)
        elif len(records) > 1:
            output_str += "\nMore than one matching archive found. Not deleted"
            rows = list(map(list, records)) # Convert tuple of tuples to list of lists
            data = [header]
            data.extend(rows)
            table = SingleTable([list(map(str,row)) for row in data]) # Convert all items in inner-list of lists to strings
            #table.inner_heading_row_border = False
            output_str += table.table
            output_str += "\nUse SQL statement - DELETE FROM archive_name WHERE archive_sha1 LIKE '<checksum>' instead"
        else:
            output_str += "{} deleted successfully from database '{}'".format(archive, database)
        db.close()
        return output_str

    except sqlite3.Error as e:
        db.close()
        exceptMsg = "ERROR! Could not delete archive from database.\n\nSqlite3 said : \"{}\"".format(e)
        return exceptMsg

def reset_db(database):
	assert_argument_present(database, "-db/--database", "-r/-reset")
	output_str = ""
	try:
		output_str += "Resetting database '{}' ... ".format(database)
		db = Database(database)
		db.resetDB()
		db.close()
		output_str += "Done"
		return output_str

	except sqlite3.Error as e:
		db.close()
		return "ERROR! Could not reset database. Sqlite3 said: \"{}\"".format(e)

def create_db(database):
	assert_argument_present(database, "-db/--database", "-c/--create")
	output_str = ""
	try:
		output_str += "Now creating database  '{}' ...".format(database)
		db = Database(database)
		db.initDB()
		db.close()
		output_str += "Done"
		return output_str

	except sqlite3.Error as e:
		db.close()
		return "ERROR! Could not create database.\n\nSqlite3 said: \"{}\"".format(e)

def run_sql_query(database, sql):
	assert_argument_present(database, "-db/--database", "-s/--sql")
	output_str = ""
	try:
		db = Database(database)
		header, records = db.runSQL(sql)
		rows = list(map(list, records)) # Convert tuple of tuples to list of lists
		data = [header]
		data.extend(rows)
		table = SingleTable([list(map(str,row)) for row in data]) # Convert all items in inner-list of lists to strings
		#table.inner_heading_row_border = False
		output_str += table.table
		output_str += "\n\n{} row(s) affected".format(len(rows))
		db.close()
		return output_str

	except sqlite3.Error as e:
		db.close()
		return "ERROR! Could not run query.\n\nSqlite3 said : \"{}\"".format(e)
	except TypeError as e:
		db.close()
		return "ERROR! Could not run query.\n\nSqlite3 said : \"{}\"".format(e)

def get_database_schema(database):
	output_str = ""
	try:
		db = Database(database)
		sql = "SELECT name as 'Table Name', type as 'Type' FROM sqlite_master WHERE type='table' OR type='view' ORDER BY name"
		header, records = db.runSQL(sql)
		rows = list(map(list, records)) # Convert tuple of tuples to list of lists
		data = [header]
		data.extend(rows)
		table = SingleTable([list(map(str,row)) for row in data]) # Convert all items in inner-list of lists to strings
		#table.inner_heading_row_border = False
		output_str += "{} table(s)/view(s) found\n\n".format(len(rows))
		output_str += table.table

		if len(rows) > 0:
			output_str += "\n\n --------- Column info for table(s)/view(s) -------"
			for row in rows:
				output_str += "\n"
				table_name = row[0]
				sql = "PRAGMA table_info('{}')".format(table_name)
				header, records = db.runSQL(sql)
				rows = list(map(list, records)) # Convert tuple of tuples to list of lists
				data = [header]
				data.extend(rows)
				data = [list(map(str,row)) for row in data]
				#table = SingleTable([list(map(str,row)) for row in data]) # Convert all items in inner-list of lists to strings
				#table.inner_heading_row_border = False
				output_str += create_report(data,table_name)
		db.close()
		return output_str

	except sqlite3.Error as e:
		db.close()
		return "ERROR! Could not run query.\n\nSqlite3 said : \"{}\"".format(e)

def backup_database(database):
	output_str = ""
	try:
		dir = os.path.dirname(os.path.abspath(database))
		filename, ext = os.path.splitext(os.path.basename(database))
		datetime_str = time.strftime("%Y-%m-%dT%H%M%S", time.localtime())
		backup_str = "_backup_" + datetime_str
		backup_file = os.path.join(dir, filename+backup_str+ext)
		shutil.copy(database, backup_file)
		return "Backup created!\n\nOriginal - '{}'\nBackup   - '{}'".format(database, backup_file)
	except WindowsError as e:
		return "ERROR! Unable to backup database.\n\nMS-Windows says: \"{}\"".format(e)
