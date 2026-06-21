import os
import shutil
import sqlite3
import tempfile

from iphone_backup_decrypt import EncryptedBackup, RelativePath

from export_calls import apple_timestamp_to_datetime, build_contact_lookup, suppress_size_warnings
from export_whatsapp import WHATSAPP_DOMAIN, WHATSAPP_DB_PATH, MESSAGE_TYPES, SESSION_TYPES
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
        self.whatsapp_db = None
        self.contact_lookup = {}

    def load_databases(self):
        """Extract both databases to the temp folder and build contact lookup."""
        backup = EncryptedBackup(backup_directory=self.backup_dir, passphrase=self.passphrase)
        self.contact_lookup = build_contact_lookup(backup)

        # Extract Calls DB
        calls_path = os.path.join(self.temp_dir, "calls.sqlite")
        try:
            with suppress_size_warnings():
                backup.extract_file(relative_path=RelativePath.CALL_HISTORY, output_filename=calls_path)
            self.calls_db = sqlite3.connect(calls_path, check_same_thread=False)
            self.calls_db.row_factory = sqlite3.Row
        except Exception:
            app_logger.error("Errore estrazione Calls DB per Viewer", exc_info=True)

        # Extract SMS DB
        sms_path = os.path.join(self.temp_dir, "sms.sqlite")
        try:
            with suppress_size_warnings():
                backup.extract_file(relative_path=RelativePath.TEXT_MESSAGES, output_filename=sms_path)
            self.sms_db = sqlite3.connect(sms_path, check_same_thread=False)
            self.sms_db.row_factory = sqlite3.Row
        except Exception:
            app_logger.error("Errore estrazione SMS DB per Viewer", exc_info=True)

        # Extract WhatsApp DB
        wa_path = os.path.join(self.temp_dir, "whatsapp.sqlite")
        try:
            with suppress_size_warnings():
                backup.extract_file(
                    relative_path=RelativePath.WHATSAPP_MESSAGES,
                    domain_like="%whatsapp%",
                    output_filename=wa_path,
                )
            self.whatsapp_db = sqlite3.connect(wa_path, check_same_thread=False)
            self.whatsapp_db.row_factory = sqlite3.Row
        except FileNotFoundError:
            app_logger.info("WhatsApp non trovato nel backup (normale se non installato).")
        except Exception:
            app_logger.error("Errore estrazione WhatsApp DB per Viewer", exc_info=True)

        # Clean up backup object to avoid cross-thread SQLite issues on __del__
        import gc
        gc.collect()
        try:
            if hasattr(backup, "_cleanup"):
                backup._cleanup()
                backup._cleanup = lambda *args, **kwargs: None
        except Exception:
            pass

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
            if raw_date > 10**16:
                ts = (raw_date / 1e9) + APPLE_EPOCH_OFFSET
            elif raw_date > 10**13:
                ts = (raw_date / 1e6) + APPLE_EPOCH_OFFSET
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

    def search_whatsapp(self, search_term: str = "", limit: int = 200):
        if not self.whatsapp_db:
            return []

        query = """
            SELECT
                m.ZMESSAGEDATE, m.ZTEXT, m.ZISFROMME, m.ZMESSAGETYPE,
                s.ZPARTNERNAME, s.ZCONTACTJID, s.ZSESSIONTYPE
            FROM ZWAMESSAGE m
            JOIN ZWACHATSESSION s ON m.ZCHATSESSION = s.Z_PK
            WHERE m.ZTEXT LIKE ? OR s.ZPARTNERNAME LIKE ? OR s.ZCONTACTJID LIKE ?
            ORDER BY m.ZMESSAGEDATE DESC
            LIMIT ?
        """
        like_term = f"%{search_term}%"
        try:
            rows = self.whatsapp_db.execute(query, (like_term, like_term, like_term, limit)).fetchall()
        except Exception:
            app_logger.error("Errore ricerca WhatsApp", exc_info=True)
            return []

        results = []
        for row in rows:
            dt = apple_timestamp_to_datetime(row["ZMESSAGEDATE"])
            dt_str = dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""
            direction = "Inviato" if row["ZISFROMME"] else "Ricevuto"
            partner = row["ZPARTNERNAME"] or row["ZCONTACTJID"] or ""
            text = row["ZTEXT"] or ""
            msg_type = MESSAGE_TYPES.get(row["ZMESSAGETYPE"], "altro")
            session_type = SESSION_TYPES.get(row["ZSESSIONTYPE"], "")

            if not text:
                text = f"[{msg_type}]"

            results.append((dt_str, partner, direction, session_type, text.replace("\n", " ")))

        return results

    def get_whatsapp_sessions(self) -> list[dict]:
        """Return a list of WhatsApp sessions with metadata for the chat list."""
        if not self.whatsapp_db:
            return []

        query = """
            SELECT
                s.Z_PK,
                s.ZPARTNERNAME,
                s.ZCONTACTJID,
                s.ZSESSIONTYPE,
                COUNT(m.Z_PK) as msg_count,
                MAX(m.ZMESSAGEDATE) as last_date
            FROM ZWACHATSESSION s
            LEFT JOIN ZWAMESSAGE m ON m.ZCHATSESSION = s.Z_PK
            GROUP BY s.Z_PK
            HAVING msg_count > 0
            ORDER BY last_date DESC
        """
        try:
            rows = self.whatsapp_db.execute(query).fetchall()
        except Exception:
            app_logger.error("Errore caricamento sessioni WhatsApp", exc_info=True)
            return []

        sessions = []
        for row in rows:
            dt = apple_timestamp_to_datetime(row["last_date"])
            sessions.append({
                "session_id": row["Z_PK"],
                "partner_name": row["ZPARTNERNAME"] or "",
                "contact_jid": row["ZCONTACTJID"] or "",
                "session_type": SESSION_TYPES.get(row["ZSESSIONTYPE"], ""),
                "session_type_raw": row["ZSESSIONTYPE"],
                "message_count": row["msg_count"],
                "last_date": dt.strftime("%Y-%m-%d %H:%M") if dt else "",
            })

        return sessions

    def get_whatsapp_messages(self, session_id: int, limit: int = 500) -> list[tuple]:
        """Return messages for a specific WhatsApp session."""
        if not self.whatsapp_db:
            return []

        query = """
            SELECT
                ZMESSAGEDATE, ZTEXT, ZISFROMME, ZMESSAGETYPE, ZFROMJID
            FROM ZWAMESSAGE
            WHERE ZCHATSESSION = ?
            ORDER BY ZMESSAGEDATE ASC
            LIMIT ?
        """
        try:
            rows = self.whatsapp_db.execute(query, (session_id, limit)).fetchall()
        except Exception:
            app_logger.error("Errore caricamento messaggi WhatsApp", exc_info=True)
            return []

        results = []
        for row in rows:
            dt = apple_timestamp_to_datetime(row["ZMESSAGEDATE"])
            dt_str = dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""
            direction = "Inviato" if row["ZISFROMME"] else "Ricevuto"
            text = row["ZTEXT"] or ""
            msg_type = MESSAGE_TYPES.get(row["ZMESSAGETYPE"], "altro")
            from_jid = row["ZFROMJID"] or ""

            if not text:
                text = f"[{msg_type}]"

            results.append((dt_str, direction, from_jid, text.replace("\n", " ")))

        return results

    def close(self):
        if self.calls_db:
            self.calls_db.close()
        if self.sms_db:
            self.sms_db.close()
        if self.whatsapp_db:
            self.whatsapp_db.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
