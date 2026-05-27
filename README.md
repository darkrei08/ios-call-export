# ios-call-export

Export iPhone call history from an encrypted local backup to CSV. Includes contact name resolution, FaceTime, and third-party app calls (WhatsApp, Teams, etc.).

## Prerequisites

- macOS (or Windows/Linux with an iTunes backup)
- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- An **encrypted** local iPhone backup (call history is only included in encrypted backups)

## Creating an encrypted backup

1. Connect your iPhone to your Mac
2. Open **Finder**, select your iPhone in the sidebar
3. Check **Encrypt local backup** and set a passphrase (remember it!)
4. Click **Back Up Now** and wait for it to complete

Backups are stored in `~/Library/Application Support/MobileSync/Backup/`.

## Installation

```bash
git clone <this-repo>
cd ios-call-export
uv sync
```

## Usage

```bash
uv run python export_calls.py
```

The script auto-detects the most recent backup and outputs `calls.csv`.

### Options

```
--backup-dir PATH    Path to a specific backup directory
--output, -o PATH    Output CSV path (default: calls.csv)
--passphrase TEXT    Backup encryption passphrase
```

### Passphrase configuration

Copy the example env file and configure your passphrase:

```bash
cp .env.example .env
```

Edit `.env` and uncomment one of the options:

- **`BACKUP_PASSPHRASE`** -- set the passphrase directly
- **`OP_BACKUP_REF`** -- use a [1Password secret reference](https://developer.1password.com/docs/cli/secret-references/) (requires [`op` CLI](https://developer.1password.com/docs/cli/), triggers biometric prompt)

The passphrase is resolved in this order:

1. `--passphrase` command-line argument
2. `BACKUP_PASSPHRASE` environment variable (via `.env` or shell)
3. `OP_BACKUP_REF` environment variable (via `.env` or shell)
4. Interactive prompt

## CSV output

| Column | Description |
|---|---|
| `id` | Database primary key |
| `unique_id` | Stable UUID for the call record |
| `start` | Call start time (ISO 8601 with timezone) |
| `end` | Call end time (ISO 8601 with timezone) |
| `contact_name` | Resolved contact name from AddressBook |
| `phone_number` | Phone number or email (for FaceTime) |
| `duration` | Human-readable duration (e.g. `5:08`) |
| `duration_seconds` | Duration as integer seconds |
| `direction` | `Incoming`, `Outgoing`, or `Missed` |
| `call_type` | `Phone`, `FaceTime Video`, `FaceTime Audio`, or app name (e.g. `Whatsapp`) |
| `answered` | `True` or `False` |
| `country_code` | ISO country code (e.g. `DE`) |
| `service_provider` | Bundle ID of the calling service |
| `location` | Location string if available |

## How it works

1. Decrypts the encrypted iOS backup using [iphone-backup-decrypt](https://github.com/KnugiHK/iphone_backup_decrypt)
2. Extracts the `AddressBook.sqlitedb` to build a phone number/email to contact name lookup
3. Extracts `CallHistory.storedata` and `CallHistoryTemp.storedata`, queries the `ZCALLRECORD` table
4. Deduplicates records across databases by `ZUNIQUE_ID`
5. Resolves contact names and call types, writes CSV

## Limitations

- Call history only goes back as far as iOS retains it (typically ~1 year, varies)
- Contact names are resolved from the AddressBook at backup time; deleted contacts won't have names unless the database's `ZNAME` field was populated
- Group FaceTime calls have no phone number or contact name — iOS stores participants in a separate relationship table, not in the main call record
- The backup must be encrypted (Apple excludes call history from unencrypted backups)
