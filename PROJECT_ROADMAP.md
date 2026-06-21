# iOS Backup Explorer - Roadmap & Memory

This file serves as the permanent memory and architectural roadmap for the project, tracking the evolution from "iOS Call Exporter" to a full "iOS Backup Explorer". 

## Development Strategy
- **`main` / `1.0-stable`**: Only stable, tested, and releasable code.
- **`feature/*`**: All new features must be developed on a dedicated minor branch.
- **Workflow**: Create branch -> Develop -> Debug -> Merge to main -> Tag new version.

## Roadmap

### [ ] v1.1 - File Manager & Wi-Fi Passwords
- **File Manager**: Build a GUI tab to explore backup domains (AppDomain, CameraRollDomain) and extract raw files.
- **Wi-Fi Passwords**: Extract saved networks and passwords from the Keychain to CSV.
- *Branch:* `feature/file-manager-wifi`

### [ ] v1.2 - SMS & iMessage
- Parse `sms.db`.
- Export messages maintaining chronological order (CSV/HTML/PDF).
- Extract linked media attachments (photos, videos, audio).
- *Branch:* `feature/messages`

### [x] v1.3 - WhatsApp & Telegram
- Parse WhatsApp `ChatStorage.sqlite` and Telegram local DBs.
- Export chats to readable formats including media.
- *Branch:* `feature/third-party-chats`

### [ ] v1.4 - Media (Photos & Videos)
- Scan CameraRoll.
- Use `Photos.sqlite` to restore original filenames, albums, and EXIF metadata.
- *Branch:* `feature/media-recovery`

### [ ] v1.5 - Notes & Voice Memos
- Parse Apple Notes (`NoteStore.sqlite`) to Markdown/TXT.
- Extract Voice Memos (`.m4a`) and rename them using the internal database.
- *Branch:* `feature/productivity-apps`

## Notes for Agents
- Always consult this file before starting new features.
- Update the checkboxes `[ ]` to `[x]` as features are completed.
- Ensure the backup decryption logic (which is already solid) is reused for all new extractions.
