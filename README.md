# Archive clone sniffer

Archive clone sniffer (ACS) is a simple command line utility to catalog your archive file collection. Currently only RAR and ZIP archives are supported. 

## Features
- Catalog your ZIP or RAR archives in an sqlite-3 database. 
- Compare files or archives against entries in the database or against each other
- CRC-32 checksum is used to check if matching files are already present
- SHA-1 checksum is computed to check for the uniqueness of the archive

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
python clone_sniffer.py --add -db my_sqlite_database.db -f <list of files delimited by space>
python clone_sniffer.py --add -db my_sqlite_database.db -a <ZIP or RAR archive>
```

**Comparing**
```
python clone_sniffer.py --compare -db my_sqlite_datbase.db -f <list of files delimited by space>
python clone_sniffer.py --compare -db my_sqlite_datbase.db -a <ZIP or RAR archive>
python clone_sniffer.py --compare -a <ZIP or RAR archive> -f <list of files delimited by space>
python clone_sniffer.py --compare -a <ZIP or RAR archive> -a2 <ZIP or RAR archive>
```

### Reports

Using the nifty [terminaltable](https://github.com/Robpol86/terminaltables/) package, ACS creates nicely formatted reports


