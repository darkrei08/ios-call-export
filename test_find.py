import sys
from export_calls import find_backups
from export_whatsapp import _find_whatsapp_domains
from iphone_backup_decrypt import EncryptedBackup

backups = find_backups()
backup = EncryptedBackup(backup_directory=str(backups[0]), passphrase=sys.argv[1])
try:
    print('Domains:', _find_whatsapp_domains(backup))
finally:
    pass
