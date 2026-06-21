#!/usr/bin/env python3
"""Extract WhatsApp chat history from an encrypted iOS local backup."""

import csv
import json
import os
import sqlite3
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from iphone_backup_decrypt import EncryptedBackup

import master_settings
from export_calls import (
    APPLE_EPOCH,
    IncorrectPassphraseError,
    apple_timestamp_to_datetime,
    build_contact_lookup,
    suppress_size_warnings,
)
from logger import app_logger

# WhatsApp stores its database under this domain in iOS backups
WHATSAPP_DOMAIN = "AppDomainGroup-group.net.whatsapp.WhatsApp.shared"
WHATSAPP_DB_PATH = "ChatStorage.sqlite"

# Message type constants
MESSAGE_TYPES = {
    0: "text",
    1: "image",
    2: "video",
    3: "audio",
    4: "contact",
    5: "location",
    6: "system",
    7: "link",
    8: "document",
    9: "sticker",
    14: "deleted",
    15: "gif",
}

# Session type constants
SESSION_TYPES = {
    0: "Privata",
    1: "Gruppo",
    2: "Broadcast",
}


def _extract_whatsapp_db(backup: EncryptedBackup) -> str | None:
    """Extract ChatStorage.sqlite from backup to a temp file. Returns path or None."""
    tmp_fd = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    tmp_path = tmp_fd.name
    tmp_fd.close()

    try:
        with suppress_size_warnings():
            from iphone_backup_decrypt import RelativePath
            backup.extract_file(
                relative_path=RelativePath.WHATSAPP_MESSAGES,
                domain_like="%whatsapp%",
                output_filename=tmp_path,
            )
        return tmp_path
    except FileNotFoundError:
        os.unlink(tmp_path)
        return None
    except Exception as e:
        os.unlink(tmp_path)
        err_lower = str(e).lower()
        if any(
            kw in err_lower
            for kw in ("incorrect passphrase", "failed to decrypt", "wrong password", "bad decrypt")
        ):
            raise IncorrectPassphraseError(
                "La password di decrittazione inserita non è corretta.\n"
                "Impossibile decrittare i file WhatsApp del backup.\n\n"
                "Verifica la password e riprova."
            ) from e
        raise


def _read_sessions(conn: sqlite3.Connection) -> dict[int, dict]:
    """Read all chat sessions from ZWACHATSESSION."""
    # Check which columns exist
    columns = {row[1] for row in conn.execute("PRAGMA table_info(ZWACHATSESSION)").fetchall()}

    has_partner_name = "ZPARTNERNAME" in columns
    has_contact_jid = "ZCONTACTJID" in columns
    has_session_type = "ZSESSIONTYPE" in columns
    has_message_count = "ZMESSAGECOUNT" in columns
    has_last_message_date = "ZLASTMESSAGEDATE" in columns

    select_parts = ["Z_PK"]
    if has_partner_name:
        select_parts.append("ZPARTNERNAME")
    if has_contact_jid:
        select_parts.append("ZCONTACTJID")
    if has_session_type:
        select_parts.append("ZSESSIONTYPE")
    if has_message_count:
        select_parts.append("ZMESSAGECOUNT")
    if has_last_message_date:
        select_parts.append("ZLASTMESSAGEDATE")

    query = f"SELECT {', '.join(select_parts)} FROM ZWACHATSESSION ORDER BY Z_PK"
    rows = conn.execute(query).fetchall()

    sessions = {}
    for row in rows:
        pk = row["Z_PK"]
        partner_name = row["ZPARTNERNAME"] if has_partner_name else ""
        contact_jid = row["ZCONTACTJID"] if has_contact_jid else ""
        session_type = row["ZSESSIONTYPE"] if has_session_type else 0
        message_count = row["ZMESSAGECOUNT"] if has_message_count else 0
        last_msg_date = row["ZLASTMESSAGEDATE"] if has_last_message_date else None

        # Parse last message date
        last_msg_dt = apple_timestamp_to_datetime(last_msg_date) if last_msg_date else None

        sessions[pk] = {
            "session_id": pk,
            "partner_name": partner_name or "",
            "contact_jid": contact_jid or "",
            "session_type": SESSION_TYPES.get(session_type, f"Sconosciuto ({session_type})"),
            "session_type_raw": session_type,
            "message_count": message_count or 0,
            "last_message_date": last_msg_dt.strftime("%Y-%m-%d %H:%M:%S") if last_msg_dt else "",
            "messages": [],
        }

    return sessions


def _read_messages(conn: sqlite3.Connection, sessions: dict[int, dict]) -> None:
    """Read all messages from ZWAMESSAGE and attach to sessions."""
    columns = {row[1] for row in conn.execute("PRAGMA table_info(ZWAMESSAGE)").fetchall()}

    has_text = "ZTEXT" in columns
    has_is_from_me = "ZISFROMME" in columns
    has_message_date = "ZMESSAGEDATE" in columns
    has_from_jid = "ZFROMJID" in columns
    has_message_type = "ZMESSAGETYPE" in columns
    has_chat_session = "ZCHATSESSION" in columns
    has_starred = "ZSTARRED" in columns

    if not has_chat_session:
        app_logger.warning("ZWAMESSAGE non ha la colonna ZCHATSESSION — impossibile collegare ai messaggi.")
        return

    select_parts = ["Z_PK", "ZCHATSESSION"]
    if has_text:
        select_parts.append("ZTEXT")
    if has_is_from_me:
        select_parts.append("ZISFROMME")
    if has_message_date:
        select_parts.append("ZMESSAGEDATE")
    if has_from_jid:
        select_parts.append("ZFROMJID")
    if has_message_type:
        select_parts.append("ZMESSAGETYPE")
    if has_starred:
        select_parts.append("ZSTARRED")

    query = f"SELECT {', '.join(select_parts)} FROM ZWAMESSAGE ORDER BY ZMESSAGEDATE ASC"
    rows = conn.execute(query).fetchall()

    for row in rows:
        session_id = row["ZCHATSESSION"]
        if session_id not in sessions:
            continue

        text = row["ZTEXT"] if has_text else None
        is_from_me = bool(row["ZISFROMME"]) if has_is_from_me else False
        msg_date = row["ZMESSAGEDATE"] if has_message_date else None
        from_jid = row["ZFROMJID"] if has_from_jid else ""
        msg_type_raw = row["ZMESSAGETYPE"] if has_message_type else 0
        starred = bool(row["ZSTARRED"]) if has_starred else False

        dt = apple_timestamp_to_datetime(msg_date)
        dt_local = dt.astimezone() if dt else None

        msg_type_label = MESSAGE_TYPES.get(msg_type_raw, f"altro ({msg_type_raw})")

        # Format display text based on message type
        if text:
            display_text = text
        elif msg_type_raw == 1:
            display_text = "📷 [Immagine]"
        elif msg_type_raw == 2:
            display_text = "🎬 [Video]"
        elif msg_type_raw == 3:
            display_text = "🎵 [Audio]"
        elif msg_type_raw == 4:
            display_text = "👤 [Contatto]"
        elif msg_type_raw == 5:
            display_text = "📍 [Posizione]"
        elif msg_type_raw == 6:
            display_text = "⚙️ [Messaggio di sistema]"
        elif msg_type_raw == 8:
            display_text = "📄 [Documento]"
        elif msg_type_raw == 9:
            display_text = "🎨 [Sticker]"
        elif msg_type_raw == 14:
            display_text = "🗑️ [Messaggio eliminato]"
        elif msg_type_raw == 15:
            display_text = "🎞️ [GIF]"
        else:
            display_text = f"[{msg_type_label}]"

        sessions[session_id]["messages"].append(
            {
                "msg_id": row["Z_PK"],
                "is_from_me": is_from_me,
                "text": display_text,
                "raw_text": text,
                "timestamp": dt_local.timestamp() if dt_local else 0,
                "date": dt_local.strftime("%Y-%m-%d %H:%M:%S") if dt_local else "",
                "from_jid": from_jid or "",
                "message_type": msg_type_label,
                "message_type_raw": msg_type_raw,
                "starred": starred,
            }
        )


def get_whatsapp_chats(backup_dir: str, passphrase: str) -> dict:
    """Extract WhatsApp ChatStorage.sqlite and build the chat data dictionary.

    Returns a dict keyed by session_id with session metadata and messages list.
    Returns empty dict if WhatsApp is not found in the backup.
    """
    backup = EncryptedBackup(backup_directory=backup_dir, passphrase=passphrase)

    app_logger.info("Ricerca database WhatsApp nel backup...")
    tmp_path = _extract_whatsapp_db(backup)

    if tmp_path is None:
        app_logger.warning(
            "WhatsApp non trovato nel backup. "
            "Assicurati che WhatsApp fosse installato al momento del backup."
        )
        return {}

    try:
        conn = sqlite3.connect(tmp_path)
        conn.row_factory = sqlite3.Row

        # Verify this is a WhatsApp database
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "ZWACHATSESSION" not in tables or "ZWAMESSAGE" not in tables:
            conn.close()
            app_logger.warning("Il database estratto non contiene le tabelle WhatsApp attese.")
            return {}

        sessions = _read_sessions(conn)
        _read_messages(conn, sessions)
        conn.close()

        # Update actual message counts
        for session in sessions.values():
            session["message_count"] = len(session["messages"])

        # Filter out empty sessions
        sessions = {k: v for k, v in sessions.items() if v["message_count"] > 0}

        app_logger.info(
            f"WhatsApp: trovate {len(sessions)} conversazioni con "
            f"{sum(s['message_count'] for s in sessions.values())} messaggi totali."
        )

        return sessions
    finally:
        os.unlink(tmp_path)


def export_whatsapp_to_csv_and_html(
    backup_dir: str,
    passphrase: str,
    output_html: str,
    output_csv: str,
    excel_compat: bool = True,
):
    """Main entry point to export WhatsApp chats to HTML viewer and CSV."""
    app_logger.info("Inizio estrazione chat WhatsApp...")
    chat_data = get_whatsapp_chats(backup_dir, passphrase)

    if not chat_data:
        raise ValueError(
            "Nessuna chat WhatsApp trovata nel backup.\n"
            "Assicurati che WhatsApp fosse installato al momento del backup."
        )

    # Apply exclusions
    device_name = master_settings.get_device_name(backup_dir)
    exclusions = master_settings.get_device_exclusions(device_name)

    filtered_data = {}
    excluded_count = 0
    for session_id, chat in chat_data.items():
        partner = chat.get("partner_name") or ""
        jid = chat.get("contact_jid") or ""
        if not master_settings.is_excluded(partner, jid, exclusions):
            filtered_data[session_id] = chat
        else:
            excluded_count += 1

    if excluded_count > 0:
        app_logger.info(
            f"Escluse {excluded_count} conversazioni WhatsApp "
            f"in base alle impostazioni master del dispositivo ({device_name})."
        )

    chat_data = filtered_data
    app_logger.info(f"Trovate {len(chat_data)} conversazioni WhatsApp da esportare.")

    # --- HTML EXPORT ---
    template_path = Path(__file__).parent / "assets" / "whatsapp_template.html"
    if not template_path.exists():
        app_logger.error(f"Template WhatsApp non trovato in {template_path}. Skip HTML.")
    else:
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        json_payload = json.dumps(chat_data, ensure_ascii=False)
        html_content = html_content.replace("{{ WHATSAPP_DATA_JSON }}", json_payload)

        with open(output_html, "w", encoding="utf-8") as f:
            f.write(html_content)
        app_logger.info(f"WhatsApp HTML Viewer generato: {output_html}")

    # --- CSV EXPORT ---
    sep = ";" if excel_compat else ","
    with open(output_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=sep)
        writer.writerow(
            [
                "Chat",
                "JID",
                "Tipo Chat",
                "Data",
                "Direzione",
                "Mittente JID",
                "Tipo Messaggio",
                "Testo",
                "Preferito",
            ]
        )

        for session_id, chat in chat_data.items():
            partner = chat.get("partner_name") or chat.get("contact_jid") or f"Chat {session_id}"
            jid = chat.get("contact_jid") or ""
            chat_type = chat.get("session_type") or ""

            for msg in chat["messages"]:
                direction = "Inviato" if msg["is_from_me"] else "Ricevuto"
                text = (msg.get("raw_text") or msg.get("text") or "").replace("\n", " ")
                writer.writerow(
                    [
                        partner,
                        jid,
                        chat_type,
                        msg["date"],
                        direction,
                        msg.get("from_jid", ""),
                        msg.get("message_type", ""),
                        text,
                        "⭐" if msg.get("starred") else "",
                    ]
                )

    app_logger.info(f"WhatsApp CSV generato: {output_csv}")

    # --- Summary ---
    total_msgs = sum(c["message_count"] for c in chat_data.values())
    private = sum(1 for c in chat_data.values() if c["session_type_raw"] == 0)
    groups = sum(1 for c in chat_data.values() if c["session_type_raw"] == 1)

    app_logger.info("\n--- WhatsApp Export Summary ---")
    app_logger.info(f"Conversazioni totali: {len(chat_data)}")
    app_logger.info(f"Messaggi totali:      {total_msgs}")
    app_logger.info(f"Chat private:         {private}")
    app_logger.info(f"Gruppi:               {groups}")
    app_logger.info("-------------------------------\n")

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
    out_html = str(export_dir / "WhatsApp_Viewer.html")
    out_csv = str(export_dir / "whatsapp.csv")
    export_whatsapp_to_csv_and_html(backup_dir, passphrase, out_html, out_csv)
