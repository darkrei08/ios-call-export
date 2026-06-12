import sys
from iphone_backup_decrypt import EncryptedBackup

def get_backup_files(backup_dir: str, passphrase: str) -> list[dict]:
    """Return a list of files available in the encrypted backup."""
    backup = EncryptedBackup(backup_directory=backup_dir, passphrase=passphrase)
    files = []
    
    with backup.manifest_db_cursor() as cur:
        # SQLite query to get all non-directory files (flags=1 usually means file, 2=dir)
        # We fetch domain and relativePath
        cur.execute("SELECT domain, relativePath, flags FROM Files WHERE flags = 1")
        for row in cur.fetchall():
            domain = row[0]
            rel_path = row[1]
            if rel_path:
                files.append({
                    "domain": domain,
                    "relativePath": rel_path
                })
    return files
