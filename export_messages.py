import csv
import json
import os
import sqlite3
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from iphone_backup_decrypt import EncryptedBackup, RelativePath

import master_settings
from export_calls import IncorrectPassphraseError, build_contact_lookup
from logger import app_logger

# iOS dates are typically measured in seconds from Jan 1, 2001
APPLE_EPOCH_OFFSET = 978307200


def get_messages_data(backup_dir: str, passphrase: str) -> dict:
    """Extract sms.db and build the messages dictionary grouped by handle."""
    backup = EncryptedBackup(backup_directory=backup_dir, passphrase=passphrase)

    app_logger.info("Building contact lookup from AddressBook...")
    contact_lookup = build_contact_lookup(backup)

    tmp_path = tempfile.mktemp(suffix=".sqlite")
    try:
        app_logger.info("Extracting sms.db...")
        # Redirect stdout temporarily if library is noisy
        backup.extract_file(relative_path=RelativePath.TEXT_MESSAGES, output_filename=tmp_path)
    except Exception as e:
        err_lower = str(e).lower()
        if (
            "incorrect passphrase" in err_lower
            or "failed to decrypt" in err_lower
            or "wrong password" in err_lower
            or "bad decrypt" in err_lower
        ):
            raise IncorrectPassphraseError(
                "La password di decrittazione inserita non è corretta.\n"
                "Impossibile decrittare i messaggi del backup.\n\n"
                "Verifica la password e riprova."
            ) from e
        raise Exception(f"Errore durante l'estrazione di sms.db: {e}")

    try:
        conn = sqlite3.connect(tmp_path)
        conn.row_factory = sqlite3.Row

        # Querying messages
        # Note: in iOS 14+, 'date' might be nanoseconds. We check length or magnitude.
        query = """
            SELECT 
                m.ROWID as msg_id,
                h.id as phone,
                m.text,
                m.is_from_me,
                m.date,
                m.service
            FROM message m
            LEFT JOIN handle h ON m.handle_id = h.ROWID
            WHERE h.id IS NOT NULL
            ORDER BY m.date ASC
        """

        rows = conn.execute(query).fetchall()
        conn.close()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    chat_data = {}

    for row in rows:
        handle_id = row["phone"]
        if not handle_id:
            continue

        # Normalize handle_id for contact lookup if it's a phone number
        lookup_key = handle_id.replace(" ", "")
        contact_name = contact_lookup.get(lookup_key) or contact_lookup.get(handle_id)

        if handle_id not in chat_data:
            chat_data[handle_id] = {
                "handle_id": handle_id,
                "contact_name": contact_name,
                "messages": [],
            }

        raw_date = row["date"]
        # Handle iOS 10+ nano seconds timestamp (18 digits) vs iOS 9 seconds
        if raw_date > 10**16:
            timestamp = (raw_date / 1e9) + APPLE_EPOCH_OFFSET
        elif raw_date > 10**13:
            timestamp = (raw_date / 1e6) + APPLE_EPOCH_OFFSET
        else:
            timestamp = raw_date + APPLE_EPOCH_OFFSET

        chat_data[handle_id]["messages"].append(
            {
                "is_from_me": bool(row["is_from_me"]),
                "text": row["text"],
                "timestamp": timestamp,
                "service": row["service"],
            }
        )

    return chat_data


def export_messages_to_csv_and_html(
    backup_dir: str,
    passphrase: str,
    output_html: str,
    output_csv: str,
    excel_compat: bool = True,
):
    """Main entry point to build the HTML viewer and the CSV export."""
    app_logger.info("Inizio estrazione messaggi...")
    chat_data = get_messages_data(backup_dir, passphrase)

    device_name = master_settings.get_device_name(backup_dir)
    exclusions = master_settings.get_device_exclusions(device_name)

    filtered_chat_data = {}
    excluded_count = 0
    for handle_id, chat in chat_data.items():
        contact_name = chat.get("contact_name") or ""
        if not master_settings.is_excluded(contact_name, handle_id, exclusions):
            filtered_chat_data[handle_id] = chat
        else:
            excluded_count += 1

    if excluded_count > 0:
        app_logger.info(
            f"Escluse {excluded_count} conversazioni in base alle impostazioni master del dispositivo ({device_name})."
        )

    chat_data = filtered_chat_data
    app_logger.info(f"Trovate conversazioni per {len(chat_data)} contatti.")

    # --- HTML EXPORT ---
    template_path = Path(__file__).parent / "assets" / "messages_template.html"
    if not template_path.exists():
        raise FileNotFoundError(f"Template non trovato in {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    json_payload = json.dumps(chat_data, ensure_ascii=False)
    html_content = html_content.replace("{{ CHAT_DATA_JSON }}", json_payload)

    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    app_logger.info(f"File Viewer generato con successo: {output_html}")

    # --- CSV EXPORT ---
    sep = ";" if excel_compat else ","
    with open(output_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=sep)
        writer.writerow(["Contact", "Phone/ID", "Date", "Direction", "Service", "Text"])

        for handle_id, chat in chat_data.items():
            contact_name = chat.get("contact_name") or handle_id
            for msg in chat["messages"]:
                dt_str = datetime.fromtimestamp(msg["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                direction = "Sent" if msg["is_from_me"] else "Received"
                # Prevent excel formula injection for phone numbers
                phone_out = f'="{handle_id}"' if excel_compat and str(handle_id).startswith("+") else handle_id

                writer.writerow(
                    [
                        contact_name,
                        phone_out,
                        dt_str,
                        direction,
                        msg["service"],
                        msg["text"],
                    ]
                )
    app_logger.info(f"File CSV generato con successo: {output_csv}")

    return len(chat_data)


if __name__ == "__main__":
    from export_calls import find_backups

    backups = find_backups()
    if not backups:
        app_logger.info("Nessun backup trovato.")
        sys.exit(1)

    backup_dir = str(backups[0])
    passphrase = input("Inserisci password del backup: ")
    desktop = Path.home() / "Desktop"
    export_dir = desktop if desktop.exists() else Path.home()
    out_html = str(export_dir / "Messages_Viewer.html")
    out_csv = str(export_dir / "messages.csv")
    export_messages_to_csv_and_html(backup_dir, passphrase, out_html, out_csv)
