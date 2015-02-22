__author__ = 'imad'


from zipfile import *
from rarfile import *
from terminaltables import SingleTable
import archiveclonesniffer
import os
import os.path
import sqlite3
import sys

class Database:
    def __init__(self, dbname):
        self.conn = sqlite3.connect(dbname);
        self.conn.execute('PRAGMA foreign_keys = ON')
        self.cursor = self.conn.cursor()
        self.name = dbname

    def initDB(self):
        stmt_ddl = """
        CREATE TABLE archive (
            archive_name TEXT,
            archive_size INTEGER,
            archive_sha1 TEXT( 40 )  PRIMARY KEY
                                     NOT NULL
        );
        wCREATE TABLE archive_contents (
            filename      TEXT,
            path          TEXT,
            file_size     INTEGER,
            compress_size INTEGER,
            crc32         TEXT,
            archive_id            REFERENCES ARCHIVE ( archive_sha1 ) ON DELETE CASCADE
        );
        CREATE VIEW archive_stats AS
            SELECT A.archive_name,
                A.archive_size,
                A.archive_sha1,
                count( * ) as total_files
            FROM archive_contents AS C
              JOIN archive AS A
                ON ( A.archive_sha1 = C.archive_id )
            WHERE C.file_size != 0
            GROUP BY A.archive_sha1;
        """
        self.cursor.executescript(stmt_ddl)
        #self.commit()

    def resetDB(self):
        stmt =  """
             DROP TABLE IF EXISTS archive;
             DROP TABLE IF EXISTS archive_contents;
             DROP VIEW  IF EXISTS archive_stats;
             """
        self.cursor.executescript(stmt)
        #self.conn.commit();
        self.initDB()
        print "Database Re-initialized"

    def addArchiveInfo(self, archiveInfo):
        payload = [archiveInfo]
        self.cursor.executemany('INSERT INTO archive VALUES(?, ?, ?)', payload)
        self.commit()

    def addArchiveContents(self, archiveContents):
        #self.cursor.executemany('INSERT INTO archive_contents VALUES(?, ?, ?, ?, ?, ?)', archiveContents);
        for member in archiveContents:
            record = ([member.name, member.path, member.file_size, member.compress_size, member.crc32, member.archive_sha1])
            self.cursor.execute('INSERT INTO archive_contents VALUES(?, ?, ?, ?, ?, ?)', record);

        self.commit();

    def commit(self):
        self.conn.commit();

    def close(self):
        self.conn.close()

    def addArchivetoDB(self, archive):
        self.addArchiveInfo(archive.getArchiveInfo())
        self.addArchiveContents(archive.getArchiveContents())

    def getArchiveFileCount(self, archive):
        qry = "SELECT * FROM archive_stats WHERE archive_name LIKE '{}'".format(archive)
        results = self.cursor.execute(qry)
        return results.fetchone()

    def runSQL(self, stmt):
        results = self.cursor.execute(stmt)
        desc = self.cursor.description
        cols = [col[0] for col in desc]
        return cols, results.fetchall()

    def deleteArchive(self, archive):
        qry = "SELECT * FROM archive WHERE archive_name LIKE '{}'".format(archive)
        results = self.cursor.execute(qry)
        records = results.fetchall()
        if len(records) == 0:
            return None, records
        if len(records) > 1:
            desc = self.cursor.description
            cols = [col[0] for col in desc]
            return cols, records
        qry = "DELETE FROM archive WHERE archive_name LIKE '{}'".format(archive)
        print qry
        results = self.cursor.execute(qry)
        records = results.fetchall()
        self.commit()
        return [], records

class Archive:
    def __init__(self, archive_name):
        self.archive_name = os.path.basename(archive_name)
        self.archive_path = os.path.abspath(archive_name)
        self.extension = os.path.splitext(archive_name)[1]
        self.contents = []
        self.total_files = 0
        self.updateArchiveInfo()

    def updateArchiveInfo(self):
        # Reason archive_size and sha1 attributes are set here are because they are dynamic
        # Calling this proc will update the attributes should the archive change at runtime
        self.archive_size = os.stat(self.archive_path).st_size;
        self.sha1 = archiveclonesniffer.getSHA1(self.archive_path)

    def getArchiveInfo(self):
        self.updateArchiveInfo()
        return (self.archive_name, self.archive_size, self.sha1)

    def getArchiveContents(self):
        self.getArchiveInfo();
        if self.extension == ".zip":
            archive = ZipFile
        elif self.extension == ".rar":
            archive = RarFile
        else:
            print "Unknown archive extension"
            sys.exit(-1)

        with archive(self.archive_path, 'r') as afile:
            members = afile.infolist()
            sorted_m = sorted(members, key=lambda x: x.filename)
            for m in sorted_m:
                checksum = "{:08x}".format(m.CRC)
                path, name = os.path.split(m.filename)
                if (self.extension == '.rar' and m.isdir()) or name == "Thumbs.db" :
                    continue
                if m.file_size > 0:
                    self.total_files += 1
                    member = ArchiveContent(name, path, m.file_size, m.compress_size, checksum, self.sha1)
                    self.contents.append(member)

        return self.contents

class ArchiveContent:
    def __init__(self, name, path, file_size, compress_size, crc32, archive_sha1 ):
        self.name = name
        self.path = path
        self.file_size = file_size
        self.compress_size = compress_size
        self.crc32 = crc32
        self.archive_sha1 = archive_sha1

    def debug_msg(self):
        print self.name, self.path, self.file_size, self.compress_size, self.crc32, self.archive_sha1

class Comparator:
    # Possible comparisons
    # - archive vs. archive
    # - archive vs. database
    # - file    vs. archive
    # - file    vs. database
    def __init__(self, archive=None, reference_archive=None, database=None, files=None):
        self.archive = archive
        self.ref_archive = reference_archive
        self.database = database
        self.files = files

    def compare(self):
        if self.target_archive != None:
            self.compareArchivexArchive()
        elif self.database != None:
            self.compareArchivexDatabase()
        else:
            print "Need to specify database or archive to compare against"
            system.exit(-2)

    def debug_tbl(self, data):
        table = SingleTable(data, "Debug")
        print table.table

    def findFileinDB(self, file_crc32):
        table_contents = "archive_contents"
        table_archive = "archive"
        field_filename = table_contents + ".filename"
        field_archivename = table_archive + ".archive_name"
        field_path = table_contents + ".path"
        field_filesize = table_contents + ".file_size"
        field_crc32= table_contents + ".crc32"
        field_archive_id = table_contents + ".archive_id"
        field_archive_sha1 = table_archive + ".archive_sha1"
        operator = "LIKE"
        key = file_crc32
        qry = """ SELECT {},{},{},{},{}
                    FROM {}
                        JOIN {}
                            ON ({} = {})
                    WHERE {} {} '{}'
                    AND
                    {} != 0
                """.format( field_filename, field_archivename, field_path, field_filesize, field_crc32,
                            table_contents,
                            table_archive,
                            field_archive_id, field_archive_sha1,
                            field_crc32, operator, key,
                            field_filesize
                    )
        # print qry
        self.database.cursor.execute(qry)
        raw_results = self.database.cursor.fetchall() # Name, Archive, Path, Size, CRC32
        return raw_results

    def compareFilexArchive(self, files_or_archive = None, ref_archive = None):
        # Compare files or archive against archive depending on what is passed as argument

        archive_vs_archive = False
        archive_stats = [['Archive name', 'Archive Size', 'Total Files', 'Unmatched Files']] # header

        if files_or_archive is None:
            # List of files is passed
            src_filelist = self.files
            file_origin = '<FILE>'
            file_header = 'Filename'
        else:
            # Archive is passed instead of list of files
            # Get list of files from archive and proceed as usual
            archive_vs_archive = True
            src_archive = Archive(files_or_archive)
            src_filelist = src_archive.getArchiveContents()
            file_origin = src_archive.archive_name
            archive_stats.append([file_origin, humansize(src_archive.archive_size), str(src_archive.total_files)])
            file_header = 'Filename ({})'.format(file_origin)

        if ref_archive is None:
            # Only used in archive vs. archive comparison.
            # self.archive becomes the reference archive to compare against
            ref_archive = self.archive

        archive_filedict = dict()
        filedict = dict()
        archive = Archive(ref_archive)
        archiveContents = archive.getArchiveContents()
        ref_archive_name = archive.archive_name
        matching_files_header = [file_header, 'Filename ({})'.format(ref_archive_name), 'Path', 'File Size', 'CRC32']
        matching_files = [matching_files_header]
        unmatched_files = [['Filename', 'Source Archive Name/File']]

        archive_stats.append([ref_archive_name, humansize(archive.archive_size), str(archive.total_files)])

        for item in archiveContents:
            archive_filedict[item.crc32] = item

        for file in src_filelist:
            non_zero_file_size = True
            if isinstance(file, ArchiveContent):
                key = file.crc32
                filename = file.name
                if file.file_size == 0:
                    non_zero_file_size = False
            else:
                key = archiveclonesniffer.getCRC32(file)
                filename = file
            filedict[key] = filename
            if key in archive_filedict:
                file_in_archive = archive_filedict[key]
                size = file_in_archive.file_size
                if size > 0:
                    matching_files.append([filename, file_in_archive.name, '/{}'.format(file_in_archive.path), humansize(size), key])
            else:
                if non_zero_file_size:
                    unmatched_files.append([filename, file_origin])

        # Append count of unmatched files
        if archive_vs_archive:
            archive_stats[1].append(str(len(unmatched_files) - 1))

        unmatched_in_ref_archive = []
        for key in archive_filedict:
            if key not in filedict:
                filename = archive_filedict[key].name
                if archive_filedict[key].file_size > 0:
                    unmatched_in_ref_archive.append([filename, ref_archive_name])

        # Update unmatched file stats
        archive_stats[-1].append(str(len(unmatched_in_ref_archive)))
        unmatched_files.extend(unmatched_in_ref_archive)

        return matching_files, archive_stats, unmatched_files

    def compareArchivexArchive(self):
        # archive = Archive(self.archive)
        # archiveContents = archive.getArchiveContents()
        return self.compareFilexArchive(files_or_archive=self.archive, ref_archive=self.ref_archive)

    def compareArchivexDatabase(self):
        # archive = Archive(self.archive)
        # archiveContents = archive.getArchiveContents()
        # self.files = archiveContents
        return self.compareFilexDatabase(archive=self.archive)

    def compareFilexDatabase(self, archive=None):
    # Compare file(s) against entries in the database based on their CRC32 checksum
        file_heading = 'Filename'
        heading_archive_name = ''
        if archive is None:
            filelist = self.files
        else:
            archive = Archive(self.archive)
            archiveContents = archive.getArchiveContents()
            filelist = archiveContents
            heading_archive_name = ' ({})'.format(archive.archive_name)
            file_heading = file_heading + heading_archive_name

        matching_files_header = [file_heading, 'Filename (in DB)', 'Archive Name',  'Path', 'File Size', 'CRC32']
        matching_archives = set()
        unmatched_files = [['Unmatched Files' + heading_archive_name]]
        zero_byte_files = 0
        matching_files = [matching_files_header]


        for file in filelist:
            if isinstance(file,ArchiveContent):
                file_crc32 = file.crc32
                filename = file.name
                if file.file_size == 0:
                    zero_byte_files += 1
                    continue
            else:
                file_crc32 = archiveclonesniffer.getCRC32(file)
                filename = file

            raw_results = self.findFileinDB(file_crc32)
            if len(raw_results) > 0:
                for row in raw_results:
                    name_in_db, archive, path, size, crc32 = row[0], row[1], row[2], humansize(row[3]), row[4]
                    matching_files.append([filename, name_in_db, archive, '/' + path, size, crc32])
                    matching_archives.add(archive)
            else:
                unmatched_files.append([filename])

        matching_archive_count = [['Archive Name', 'Size', 'Total Files', 'SHA-1']]
        for archive in matching_archives:
            row = self.database.getArchiveFileCount(archive)
            name, size, sha1, count = row
            matching_archive_count.append([name, humansize(size), str(count), sha1])

        #num_unmatched_files = len(self.files) - (len(matching_files) - 1) - zero_byte_files

        return matching_files, matching_archive_count, unmatched_files

def humansize(nbytes):
    suffixes = ['B', 'KiB', 'MiB', 'GiB', 'TB', 'PB']
    if nbytes == 0: return '0 B'
    i = 0
    while nbytes >= 1024 and i < len(suffixes)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])

