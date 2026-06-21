# Graph Report - .  (2026-06-21)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 162 nodes · 278 edges · 19 communities (9 shown, 10 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.75)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3a7c9402`
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
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 17|Community 17]]

## God Nodes (most connected - your core abstractions)
1. `App` - 55 edges
2. `build_contact_lookup()` - 10 edges
3. `DataViewerBackend` - 8 edges
4. `IncorrectPassphraseError` - 8 edges
5. `read_calls_from_db()` - 7 edges
6. `extract_calls()` - 7 edges
7. `get_messages_data()` - 7 edges
8. `find_backups()` - 6 edges
9. `EncryptedBackup` - 6 edges
10. `export_messages_to_csv_and_html()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `README` --references--> `Call Export CLI`  [EXTRACTED]
  README.md → export_calls.py
- `README` --references--> `GUI Application`  [EXTRACTED]
  README.md → gui.py
- `README` --references--> `Webhook Sync Script`  [EXTRACTED]
  README.md → send_to_webhook.py
- `CSV Export Preview` --references--> `Call Export CLI`  [INFERRED]
  assets/csv_export_example.png → export_calls.py
- `get_backup_files()` --calls--> `EncryptedBackup`  [INFERRED]
  backup_explorer.py → export_calls.py

## Import Cycles
- 1-file cycle: `export_calls.py -> export_calls.py`
- 2-file cycle: `export_calls.py -> logger.py -> export_calls.py`

## Communities (19 total, 10 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.12
Nodes (19): datetime, Exception, find_backups(), IncorrectPassphraseError, Path, Raised when backup decryption fails due to an incorrect passphrase., export_messages_to_csv_and_html(), get_messages_data() (+11 more)

### Community 1 - "Community 1"
Cohesion: 0.15
Nodes (17): DataViewerBackend, Extract both databases to the temp folder and build contact lookup., EncryptedBackup, apple_timestamp_to_datetime(), build_contact_lookup(), extract_calls(), format_duration(), main() (+9 more)

### Community 2 - "Community 2"
Cohesion: 0.13
Nodes (21): get_device_exclusions(), get_device_name(), get_exclusions_txt_path(), get_master_settings_path(), is_excluded(), load_exclusions_from_txt(), load_master_settings(), open_exclusions_txt() (+13 more)

### Community 4 - "Community 4"
Cohesion: 0.15
Nodes (13): Calls Dashboard Dark UI, Calls Dashboard Light UI, Calls Dashboard Template, CSV Export Preview, GUI Mockup, Messages Dashboard Dark UI, Messages Dashboard Light UI, Messages Dashboard Template (+5 more)

### Community 5 - "Community 5"
Cohesion: 0.18
Nodes (3): Populate the exclusion treeview with the given contacts list., Filter the exclusion contacts treeview based on search term., Reload exclusions from the text file and merge into GUI.

### Community 9 - "Community 9"
Cohesion: 0.40
Nodes (3): get_logger(), Custom Logging Handler to save logs into a fast SQLite database.     This makes, SQLiteHandler

## Knowledge Gaps
- **14 isolated node(s):** `ios-call-export`, `run.sh script`, `Memory Log`, `Project Roadmap`, `Copilot Instructions` (+9 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `App` connect `Community 3` to `Community 0`, `Community 1`, `Community 5`, `Community 6`, `Community 7`, `Community 8`, `Community 10`, `Community 11`?**
  _High betweenness centrality (0.459) - this node is a cross-community bridge._
- **Why does `IncorrectPassphraseError` connect `Community 0` to `Community 1`, `Community 3`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `DataViewerBackend` connect `Community 1` to `Community 0`, `Community 3`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `App` (e.g. with `DataViewerBackend` and `IncorrectPassphraseError`) actually correct?**
  _`App` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Return a list of files available in the encrypted backup.`, `Extract both databases to the temp folder and build contact lookup.`, `Raised when backup decryption fails due to an incorrect passphrase.` to the rest of the system?**
  _45 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.11965811965811966 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.14855072463768115 - nodes in this community are weakly interconnected._