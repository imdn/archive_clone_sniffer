# Archive clone sniffer

Archive clone sniffer (ACS) is a simple command line utility to catalog your archive file collection. Currently only RAR and ZIP archives are supported. 

*Note*: No files are stored in the database. Only their metadata.

## Features
- Catalog your ZIP or RAR archives in an sqlite-3 database. 
- Compare files or archives against entries in the database or against each other
- CRC-32 checksum is used to check if matching files are already present
- SHA-1 checksum is computed to check for the uniqueness of the archive
- Using the nifty [terminaltable](https://github.com/Robpol86/terminaltables/) package, ACS creates nicely formatted reports

![Reporting](https://raw.githubusercontent.com/imdn/archive_clone_sniffer/master/screenshots/screen_1.png)

### Comparing files/archives
ACS also supports comparing archives for similar files independent of a database. All-in-all four comparison modes are available:

1. Compare 'list of files' against 'database' records
2. Compare 'archive' against 'database' records
3. Compare 'list of files' against 'archive'
4. Compare 'archive' against 'another archive'

To get started:

**Create a Database**

`python clone_sniffer.py --create -db my_sqlite_database.db`

**Adding files**
```
# Add list of files
python clone_sniffer.py --add -db my_sqlite_database.db -f <list of files delimited by space>
# Add an archive
python clone_sniffer.py --add -db my_sqlite_database.db -a <ZIP or RAR archive>
```

**Comparing**
```
# Check if file(s) are in database
python clone_sniffer.py --compare -db my_sqlite_datbase.db -f <list of files delimited by space>
# Check if files in archive are in database
python clone_sniffer.py --compare -db my_sqlite_datbase.db -a <ZIP or RAR archive>
# Check if file(s) are in archive
python clone_sniffer.py --compare -a <ZIP or RAR archive> -f <list of files delimited by space>
# Check if two archives contain matching files
python clone_sniffer.py --compare -a <ZIP or RAR archive> -a2 <ZIP or RAR archive>
```
**Listing files**
```
# For archive in Database
python clone_sniffer.py --list -db my_sqlite_database.db -a <ZIP or RAR archive>
# For archive
python clone_sniffer.py --list -a <ZIP or RAR archive>
```

**Delete archive from Database**

`python clone_sniffer.py --delete -db my_sqlite_database.db -a <ZIP or RAR archive>`

**Run your own SQL query on the Database**

`python clone_sniffer.py -db my_sqlite_database.db --sql <SQL Statment>`

### Known Bugs

- *Unicode support* on 2.x is shaky especially on Windows shell. Setting chcp to 65001 brings with it a different set of problems. There should be no problems with Python 3.x 




