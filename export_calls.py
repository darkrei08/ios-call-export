#!/usr/bin/env python3
"""Extract iPhone call history from an encrypted local backup to CSV."""

import argparse
import contextlib
import csv
import getpass
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv
from iphone_backup_decrypt import EncryptedBackup, RelativePath

load_dotenv()


@contextlib.contextmanager
def suppress_size_warnings():
    """Filter out the library's 'WARN: decrypted N bytes' prints, pass everything else through."""
    real_write = sys.stdout.write
    def filtered_write(s):
        if not s.startswith("WARN: decrypted"):
            return real_write(s)
        return len(s)
    sys.stdout.write = filtered_write
    try:
        yield
    finally:
        sys.stdout.write = real_write

APPLE_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)

CALL_TYPES = {
    0: "Third-Party App",
    1: "Phone",
    8: "FaceTime Video",
    16: "FaceTime Audio",
}

DEFAULT_BACKUP_DIR = Path.home() / "Library" / "Application Support" / "MobileSync" / "Backup"


def find_backups() -> list[Path]:
    if not DEFAULT_BACKUP_DIR.exists():
        return []
    return sorted(
        [p for p in DEFAULT_BACKUP_DIR.iterdir() if p.is_dir() and (p / "Manifest.db").exists()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def apple_timestamp_to_datetime(timestamp: float | None) -> datetime | None:
    if timestamp is None or timestamp == 0:
        return None
    return APPLE_EPOCH + timedelta(seconds=timestamp)


def format_duration(seconds: float | None) -> str:
    if seconds is None or seconds <= 0:
        return "0:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def normalize_phone(number: str) -> str:
    """Strip to digits only, keep last 10 for matching."""
    digits = re.sub(r"\D", "", number)
    if len(digits) > 10:
        digits = digits[-10:]
    return digits


def build_contact_lookup(backup: EncryptedBackup) -> dict[str, str]:
    """Extract AddressBook and build phone/email → display name mapping."""
    tmp_path = tempfile.mktemp(suffix=".sqlite")
    try:
        with suppress_size_warnings():
            backup.extract_file(
                relative_path=RelativePath.ADDRESS_BOOK,
                output_filename=tmp_path,
            )
    except Exception:
        print("Warning: Could not extract AddressBook — contact names will be empty", file=sys.stderr)
        return {}

    try:
        conn = sqlite3.connect(tmp_path)
        conn.row_factory = sqlite3.Row
        # property 3 = phone, property 4 = email
        rows = conn.execute("""
            SELECT
                p.First,
                p.Last,
                p.Organization,
                m.value,
                m.property
            FROM ABPerson p
            JOIN ABMultiValue m ON p.ROWID = m.record_id
            WHERE m.property IN (3, 4)
        """).fetchall()
        total_contacts = conn.execute("SELECT COUNT(*) FROM ABPerson").fetchone()[0]
        conn.close()

        lookup: dict[str, str] = {}
        phones = 0
        emails = 0
        dupes = 0
        for row in rows:
            value = row["value"]
            if not value:
                continue
            first = row["First"] or ""
            last = row["Last"] or ""
            org = row["Organization"] or ""
            name = f"{first} {last}".strip() or org
            if not name:
                continue
            if row["property"] == 3:
                key = normalize_phone(value)
                if not key:
                    continue
                phones += 1
            else:
                key = value.lower()
                emails += 1
            if key in lookup:
                dupes += 1
            lookup[key] = name

        print(f"  {total_contacts} contacts, {phones} phones, {emails} emails, {dupes} duplicates, {len(lookup)} unique keys")
        return lookup
    finally:
        os.unlink(tmp_path)


def resolve_call_type(call_type: int, service_provider: str) -> str:
    if call_type == 0 and service_provider:
        provider = service_provider.rsplit(".", 1)[-1] if "." in service_provider else service_provider
        return provider.title()
    return CALL_TYPES.get(call_type, f"Unknown ({call_type})")


CALL_HISTORY_PATHS = [
    "Library/CallHistoryDB/CallHistory.storedata",
    "Library/CallHistoryDB/CallHistoryTemp.storedata",
]


def read_calls_from_db(db_path: str, contacts: dict[str, str]) -> list[dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    columns = {row[1] for row in conn.execute("PRAGMA table_info(ZCALLRECORD)").fetchall()}
    has_unique_id = "ZUNIQUE_ID" in columns
    has_name = "ZNAME" in columns
    has_location = "ZLOCATION" in columns

    cursor = conn.execute(f"""
        SELECT
            Z_PK,
            {"ZUNIQUE_ID," if has_unique_id else ""}
            ZDATE,
            ZDURATION,
            ZADDRESS,
            {"ZNAME," if has_name else ""}
            ZCALLTYPE,
            ZORIGINATED,
            ZANSWERED,
            ZISO_COUNTRY_CODE,
            ZSERVICE_PROVIDER,
            ZDISCONNECTED_CAUSE
            {"," if has_location else ""}
            {"ZLOCATION" if has_location else ""}
        FROM ZCALLRECORD
        ORDER BY ZDATE ASC
    """)

    calls = []
    for row in cursor:
        dt = apple_timestamp_to_datetime(row["ZDATE"])
        originated = bool(row["ZORIGINATED"])
        # ZANSWERED only reflects whether *we* answered (meaningful for incoming calls).
        # For outgoing calls, use duration > 0 to determine if the other party picked up.
        answered = bool(row["ZANSWERED"]) or (originated and row["ZDURATION"] > 0)

        if not answered and not originated:
            direction = "Missed"
        elif originated:
            direction = "Outgoing"
        else:
            direction = "Incoming"

        address = row["ZADDRESS"] or ""
        contact_name = ""
        if address:
            if "@" in address:
                contact_name = contacts.get(address.lower(), "")
            else:
                contact_name = contacts.get(normalize_phone(address), "")
        if not contact_name and has_name:
            contact_name = row["ZNAME"] or ""

        service_provider = row["ZSERVICE_PROVIDER"] or ""

        duration_secs = int(row["ZDURATION"] or 0)
        end_dt = apple_timestamp_to_datetime(row["ZDATE"] + row["ZDURATION"]) if dt and row["ZDURATION"] else dt

        dt_local = dt.astimezone() if dt else None
        end_local = end_dt.astimezone() if end_dt else None

        calls.append({
            "id": row["Z_PK"],
            "unique_id": row["ZUNIQUE_ID"] if has_unique_id else "",
            "start": dt_local.isoformat() if dt_local else "",
            "end": end_local.isoformat() if end_local else "",
            "contact_name": contact_name,
            "phone_number": address,
            "duration": format_duration(row["ZDURATION"]),
            "duration_seconds": duration_secs,
            "direction": direction,
            "call_type": resolve_call_type(row["ZCALLTYPE"], service_provider),
            "answered": answered,
            "country_code": (row["ZISO_COUNTRY_CODE"] or "").upper(),
            "service_provider": service_provider,
            "location": row["ZLOCATION"] if has_location else "",
        })

    conn.close()
    return calls


def extract_calls(backup_dir: str, passphrase: str) -> list[dict]:
    backup = EncryptedBackup(backup_directory=backup_dir, passphrase=passphrase)

    print("Extracting contacts...")
    contacts = build_contact_lookup(backup)

    seen_unique_ids: set[str] = set()
    all_calls: list[dict] = []

    for rel_path in CALL_HISTORY_PATHS:
        label = rel_path.rsplit("/", 1)[-1]
        tmp_path = tempfile.mktemp(suffix=".sqlite")
        try:
            with suppress_size_warnings():
                backup.extract_file(relative_path=rel_path, output_filename=tmp_path)
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"  Skipping {label}: {e}", file=sys.stderr)
            continue

        try:
            calls = read_calls_from_db(tmp_path, contacts)
            new_count = 0
            for call in calls:
                uid = call["unique_id"]
                if uid and uid in seen_unique_ids:
                    continue
                if uid:
                    seen_unique_ids.add(uid)
                all_calls.append(call)
                new_count += 1
            print(f"  {label}: {new_count} calls")
        finally:
            os.unlink(tmp_path)

    all_calls.sort(key=lambda c: c["start"])
    return all_calls


def main():
    parser = argparse.ArgumentParser(description="Export iPhone call history to CSV")
    parser.add_argument("--backup-dir", help="Path to the iOS backup directory")
    parser.add_argument("--output", "-o", default="calls.csv", help="Output CSV path (default: calls.csv)")
    parser.add_argument("--passphrase", help="Backup encryption passphrase (or set BACKUP_PASSPHRASE env var)")
    args = parser.parse_args()

    if args.backup_dir:
        backup_dir = args.backup_dir
    else:
        backups = find_backups()
        if not backups:
            print(f"No iOS backups found in {DEFAULT_BACKUP_DIR}", file=sys.stderr)
            print("Create one via Finder > [your iPhone] > Back Up Now (with encryption enabled)", file=sys.stderr)
            sys.exit(1)

        if len(backups) == 1:
            backup_dir = str(backups[0])
            print(f"Found backup: {backup_dir}")
        else:
            print("Multiple backups found:")
            for i, b in enumerate(backups):
                mtime = datetime.fromtimestamp(b.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                print(f"  [{i}] {b.name} (modified: {mtime})")
            choice = input("Select backup number: ").strip()
            backup_dir = str(backups[int(choice)])

    passphrase = args.passphrase or os.environ.get("BACKUP_PASSPHRASE", "")
    if not passphrase:
        op_ref = os.environ.get("OP_BACKUP_REF", "")
        if op_ref and shutil.which("op"):
            try:
                result = subprocess.run(
                    ["op", "read", op_ref],
                    capture_output=True, text=True, timeout=30,
                )
                if result.returncode == 0 and result.stdout.strip():
                    passphrase = result.stdout.strip()
                    print("Passphrase loaded from 1Password")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
    if not passphrase:
        try:
            result = subprocess.run(
                ["security", "find-generic-password", "-a", os.environ.get("USER", ""), "-s", "ios-backup-passphrase", "-w"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                passphrase = result.stdout.strip()
                print("Passphrase loaded from Keychain")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
    if not passphrase:
        passphrase = getpass.getpass("Backup encryption passphrase: ")

    print("Decrypting backup...")
    calls = extract_calls(backup_dir, passphrase)

    if not calls:
        print("No call records found.", file=sys.stderr)
        sys.exit(1)

    fieldnames = ["id", "unique_id", "start", "end", "contact_name", "phone_number", "duration", "duration_seconds", "direction", "call_type", "answered", "country_code", "service_provider", "location"]
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(calls)

    print(f"Exported {len(calls)} calls to {args.output}")


if __name__ == "__main__":
    main()
