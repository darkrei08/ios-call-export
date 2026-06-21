import sys
from export_calls import find_backups
from iphone_backup_decrypt import EncryptedBackup

backups = find_backups()
backup = EncryptedBackup(backup_directory=str(backups[0]), passphrase=sys.argv[1])
try:
    with backup.manifest_db_cursor() as cur:
        cur.execute("SELECT domain, relativePath FROM Files WHERE relativePath LIKE '%ChatStorage.sqlite'")
        for row in cur.fetchall():
            print(row)
finally:
    pass
