# Graph Report - ios-call-export  (2026-06-21)

## Corpus Check
- 20 files · ~97,573 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 248 nodes · 377 edges · 34 communities (12 shown, 22 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 8 edges (avg confidence: 0.65)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e848e7c6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]

## God Nodes (most connected - your core abstractions)
1. `App` - 59 edges
2. `IncorrectPassphraseError` - 12 edges
3. `DataViewerBackend` - 11 edges
4. `apple_timestamp_to_datetime()` - 11 edges
5. `build_contact_lookup()` - 11 edges
6. `🇺🇸 English Version` - 8 edges
7. `🇮🇹 Versione Italiana` - 8 edges
8. `find_backups()` - 7 edges
9. `read_calls_from_db()` - 7 edges
10. `extract_calls()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `App` --uses--> `DataViewerBackend`  [INFERRED]
  gui.py → db_viewers.py
- `App` --uses--> `IncorrectPassphraseError`  [INFERRED]
  gui.py → export_calls.py
- `Connection` --uses--> `IncorrectPassphraseError`  [INFERRED]
  export_whatsapp.py → export_calls.py
- `EncryptedBackup` --uses--> `IncorrectPassphraseError`  [INFERRED]
  export_whatsapp.py → export_calls.py
- `get_messages_data()` --calls--> `IncorrectPassphraseError`  [EXTRACTED]
  export_messages.py → export_calls.py

## Import Cycles
- 1-file cycle: `export_calls.py -> export_calls.py`
- 2-file cycle: `export_calls.py -> logger.py -> export_calls.py`

## Communities (34 total, 22 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.10
Nodes (38): Connection, datetime, apple_timestamp_to_datetime(), build_contact_lookup(), extract_calls(), find_backups(), format_duration(), IncorrectPassphraseError (+30 more)

### Community 1 - "Community 1"
Cohesion: 0.40
Nodes (3): get_logger(), Custom Logging Handler to save logs into a fast SQLite database.     This makes, SQLiteHandler

### Community 2 - "Community 2"
Cohesion: 0.13
Nodes (21): get_device_exclusions(), get_device_name(), get_exclusions_txt_path(), get_master_settings_path(), is_excluded(), load_exclusions_from_txt(), load_master_settings(), open_exclusions_txt() (+13 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (8): App, Populate the exclusion treeview with the given contacts list., Open the plain-text exclusions file in the OS default editor., Reload exclusions from the text file and merge into GUI., Apply custom styling overrides on top of the current sv_ttk theme., Load WhatsApp sessions into the left panel., When a chat is selected in the left panel, load its messages in the right panel., Filter WhatsApp sessions and messages by search term.

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (24): Advanced Options, 🔍 Automatic Backup Discovery, Basic CLI Usage, Clean Excel Output, 📸 Demo & Interface, 💻 Developer Guide (CLI & Automation), 🇺🇸 English Version, 🚫 Excluding Contacts from Reports (+16 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (22): Applicazione Desktop Moderna (GUI), Automazione Password (`.env` o Keychain), 📄 CSV Esportato — Cosa Otterrai, Dashboard Web Interattive, 📸 Demo e Interfaccia, 🚫 Escludere Contatti dai Report, File Excel Pulito e Ordinato, 💻 Guida per Sviluppatori (CLI e Automazione) (+14 more)

### Community 6 - "Community 6"
Cohesion: 0.27
Nodes (7): Exception, extract_live_file(), get_connected_device_info(), list_live_files(), Returns the name/identifier of the connected device or raises an error., List files and directories in the given path using AFC.     Returns a list of d, Extract a file from the connected device to the local PC.

### Community 7 - "Community 7"
Cohesion: 0.17
Nodes (4): DataViewerBackend, Return a list of WhatsApp sessions with metadata for the chat list., Return messages for a specific WhatsApp session., Extract both databases to the temp folder and build contact lookup.

### Community 8 - "Community 8"
Cohesion: 0.20
Nodes (9): Development Strategy, iOS Backup Explorer - Roadmap & Memory, Notes for Agents, Roadmap, [ ] v1.1 - File Manager & Wi-Fi Passwords, [ ] v1.2 - SMS & iMessage, [ ] v1.4 - Media (Photos & Videos), [ ] v1.5 - Notes & Voice Memos (+1 more)

### Community 9 - "Community 9"
Cohesion: 0.33
Nodes (3): Filter the exclusion contacts treeview based on search term., Append a value on a new line in a ScrolledText widget, avoiding same-line concat, Remove a specific line from a ScrolledText widget, cleaning up empty lines.

## Knowledge Gaps
- **63 isolated node(s):** `ios-call-export`, `run.sh script`, `graphify`, `[Session State Snapshot] - 2026-06-20 11:24:24`, `[Session State Snapshot] - 2026-06-20 11:44:40` (+58 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `App` connect `Community 3` to `Community 0`, `Community 33`, `Community 6`, `Community 7`, `Community 9`, `Community 10`?**
  _High betweenness centrality (0.265) - this node is a cross-community bridge._
- **Why does `IncorrectPassphraseError` connect `Community 0` to `Community 3`, `Community 6`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Why does `DataViewerBackend` connect `Community 7` to `Community 0`, `Community 3`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `App` (e.g. with `DataViewerBackend` and `IncorrectPassphraseError`) actually correct?**
  _`App` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `IncorrectPassphraseError` (e.g. with `Connection` and `EncryptedBackup`) actually correct?**
  _`IncorrectPassphraseError` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Return a list of files available in the encrypted backup.`, `Extract both databases to the temp folder and build contact lookup.`, `Return a list of WhatsApp sessions with metadata for the chat list.` to the rest of the system?**
  _103 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.09663120567375887 - nodes in this community are weakly interconnected._