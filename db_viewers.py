import os
import shutil
import sqlite3
import tempfile

from iphone_backup_decrypt import EncryptedBackup, RelativePath

from export_calls import apple_timestamp_to_datetime, build_contact_lookup
from logger import app_logger

# iOS dates are typically measured in seconds from Jan 1, 2001
APPLE_EPOCH_OFFSET = 978307200


class DataViewerBackend:
    def __init__(self, backup_dir: str, passphrase: str):
        self.backup_dir = backup_dir
        self.passphrase = passphrase
        self.temp_dir = tempfile.mkdtemp()
        self.calls_db = None
        self.sms_db = None
        self.contact_lookup = {}
        self.backup = EncryptedBackup(backup_directory=backup_dir, passphrase=passphrase)

    def load_databases(self):
        """Extract both databases to the temp folder and build contact lookup."""
        self.contact_lookup = build_contact_lookup(self.backup)

        # Extract Calls DB
        calls_path = os.path.join(self.temp_dir, "calls.sqlite")
        try:
            self.backup.extract_file(relative_path=RelativePath.CALL_HISTORY, output_filename=calls_path)
            self.calls_db = sqlite3.connect(calls_path, check_same_thread=False)
            self.calls_db.row_factory = sqlite3.Row
        except Exception:
            app_logger.error("Errore estrazione Calls DB per Viewer", exc_info=True)

        # Extract SMS DB
        sms_path = os.path.join(self.temp_dir, "sms.sqlite")
        try:
            self.backup.extract_file(relative_path=RelativePath.TEXT_MESSAGES, output_filename=sms_path)
            self.sms_db = sqlite3.connect(sms_path, check_same_thread=False)
            self.sms_db.row_factory = sqlite3.Row
        except Exception:
            app_logger.error("Errore estrazione SMS DB per Viewer", exc_info=True)

    def search_calls(self, search_term: str = "", limit: int = 100):
        if not self.calls_db:
            return []

        query = """
            SELECT 
                ZDATE, ZADDRESS, ZDURATION, ZORIGINATED, ZSERVICE_PROVIDER
            FROM ZCALLRECORD
            WHERE ZADDRESS LIKE ? OR ZSERVICE_PROVIDER LIKE ?
            ORDER BY ZDATE DESC
            LIMIT ?
        """
        like_term = f"%{search_term}%"
        rows = self.calls_db.execute(query, (like_term, like_term, limit)).fetchall()

        results = []
        for row in rows:
            address = row["ZADDRESS"] or ""
            dt_str = apple_timestamp_to_datetime(row["ZDATE"]).strftime("%Y-%m-%d %H:%M:%S")
            direction = "Uscente" if row["ZORIGINATED"] else "Entrante/Persa"
            duration = int(row["ZDURATION"] or 0)
            service = row["ZSERVICE_PROVIDER"] or "Telefono"

            # Resolve name
            lookup_key = address.replace(" ", "")
            name = self.contact_lookup.get(lookup_key) or self.contact_lookup.get(address) or address

            results.append((dt_str, name, f"{duration}s", direction, service))

        return results

    def search_messages(self, search_term: str = "", limit: int = 100):
        if not self.sms_db:
            return []

        # Per i messaggi cerchiamo sia nel testo che nel numero di telefono
        query = """
            SELECT 
                m.text, m.is_from_me, m.date, m.service, h.id as phone
            FROM message m
            LEFT JOIN handle h ON m.handle_id = h.ROWID
            WHERE m.text LIKE ? OR h.id LIKE ?
            ORDER BY m.date DESC
            LIMIT ?
        """
        like_term = f"%{search_term}%"
        rows = self.sms_db.execute(query, (like_term, like_term, limit)).fetchall()

        results = []
        for row in rows:
            text = row["text"] or "[Allegato/Vuoto]"
            raw_date = row["date"]
            if raw_date > 1000000000000000000:
                ts = (raw_date / 1000000000) + APPLE_EPOCH_OFFSET
            else:
                ts = raw_date + APPLE_EPOCH_OFFSET

            from datetime import datetime

            dt_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            direction = "Inviato" if row["is_from_me"] else "Ricevuto"
            phone = row["phone"] or ""
            service = row["service"] or "SMS"

            # Resolve name
            lookup_key = phone.replace(" ", "")
            name = self.contact_lookup.get(lookup_key) or self.contact_lookup.get(phone) or phone

            results.append((dt_str, name, direction, service, text.replace("\n", " ")))

        return results

    def close(self):
        if self.calls_db:
            self.calls_db.close()
        if self.sms_db:
            self.sms_db.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
