import sys
from export_calls import find_backups
from iphone_backup_decrypt import EncryptedBackup

backups = find_backups()
backup = EncryptedBackup(backup_directory=str(backups[0]), passphrase=sys.argv[1])
try:
    with backup.manifest_db_cursor() as cur:
        cur.execute("SELECT relativePath, domain FROM Files WHERE domain LIKE '%whatsapp%' AND relativePath LIKE '%sqlite%' LIMIT 20")
        for row in cur.fetchall():
            print(row)
finally:
    pass
