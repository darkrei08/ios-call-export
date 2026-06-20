# Graph Report - ios-call-export  (2026-06-20)

## Corpus Check
- 18 files · ~257,969 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 158 nodes · 241 edges · 14 communities (8 shown, 6 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 7 edges (avg confidence: 0.71)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `16061d9e`
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
- [[_COMMUNITY_Community 12|Community 12]]

## God Nodes (most connected - your core abstractions)
1. `App` - 41 edges
2. `build_contact_lookup()` - 10 edges
3. `DataViewerBackend` - 8 edges
4. `IncorrectPassphraseError` - 8 edges
5. `read_calls_from_db()` - 7 edges
6. `extract_calls()` - 7 edges
7. `get_messages_data()` - 7 edges
8. `🇺🇸 English Version` - 7 edges
9. `🇮🇹 Versione Italiana` - 7 edges
10. `find_backups()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `get_backup_files()` --calls--> `EncryptedBackup`  [INFERRED]
  backup_explorer.py → export_calls.py
- `App` --uses--> `DataViewerBackend`  [INFERRED]
  gui.py → db_viewers.py
- `App` --uses--> `IncorrectPassphraseError`  [INFERRED]
  gui.py → export_calls.py
- `get_messages_data()` --calls--> `build_contact_lookup()`  [EXTRACTED]
  export_messages.py → export_calls.py
- `get_messages_data()` --calls--> `EncryptedBackup`  [EXTRACTED]
  export_messages.py → export_calls.py

## Import Cycles
- 1-file cycle: `export_calls.py -> export_calls.py`
- 2-file cycle: `export_calls.py -> logger.py -> export_calls.py`

## Communities (14 total, 6 thin omitted)

### Community 1 - "Community 1"
Cohesion: 0.12
Nodes (19): datetime, Exception, find_backups(), IncorrectPassphraseError, Raised when backup decryption fails due to an incorrect passphrase., export_messages_to_csv_and_html(), get_messages_data(), Main entry point to build the HTML viewer and the CSV export. (+11 more)

### Community 2 - "Community 2"
Cohesion: 0.15
Nodes (17): DataViewerBackend, Extract both databases to the temp folder and build contact lookup., EncryptedBackup, apple_timestamp_to_datetime(), build_contact_lookup(), extract_calls(), format_duration(), main() (+9 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (21): Advanced Options, 🔍 Automatic Backup Discovery, Basic CLI Usage, Clean Excel Output, 📸 Demo & Interface, 💻 Developer Guide (CLI & Automation), 🇺🇸 English Version, 📋 Exported CSV Fields (+13 more)

### Community 4 - "Community 4"
Cohesion: 0.11
Nodes (19): Applicazione Desktop Moderna (GUI), Automazione Password (`.env` o Keychain), 📄 CSV Esportato — Cosa Otterrai, Dashboard Web Interattive, 📸 Demo e Interfaccia, File Excel Pulito e Ordinato, 💻 Guida per Sviluppatori (CLI e Automazione), 🚀 Guida Rapida (Per Tutti gli Utenti) (+11 more)

### Community 5 - "Community 5"
Cohesion: 0.20
Nodes (9): Development Strategy, iOS Backup Explorer - Roadmap & Memory, Notes for Agents, Roadmap, [ ] v1.1 - File Manager & Wi-Fi Passwords, [ ] v1.2 - SMS & iMessage, [ ] v1.3 - WhatsApp & Telegram, [ ] v1.4 - Media (Photos & Videos) (+1 more)

### Community 6 - "Community 6"
Cohesion: 0.40
Nodes (3): get_logger(), Custom Logging Handler to save logs into a fast SQLite database.     This makes, SQLiteHandler

## Knowledge Gaps
- **42 isolated node(s):** `ios-call-export`, `run.sh script`, `graphify`, `[Session State Snapshot] - 2026-06-20 11:24:24`, `Development Strategy` (+37 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `App` connect `Community 0` to `Community 1`, `Community 2`, `Community 7`?**
  _High betweenness centrality (0.221) - this node is a cross-community bridge._
- **Why does `DataViewerBackend` connect `Community 2` to `Community 0`, `Community 1`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `IncorrectPassphraseError` connect `Community 1` to `Community 0`, `Community 2`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `App` (e.g. with `DataViewerBackend` and `IncorrectPassphraseError`) actually correct?**
  _`App` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Return a list of files available in the encrypted backup.`, `Extract both databases to the temp folder and build contact lookup.`, `Raised when backup decryption fails due to an incorrect passphrase.` to the rest of the system?**
  _57 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.09759759759759759 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.11965811965811966 - nodes in this community are weakly interconnected._