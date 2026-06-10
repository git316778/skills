# Artifact Backup Reference

Full implementation of conversation-artifact scanning, deduplication, and smart upload.

## Smart Backup Script

Full script at `C:\Users\Administrator\AppData\Local\hermes\scripts\hermes_smart_backup.py`.

### Modes

| Mode | Command |
|------|---------|
| Full run (backup + artifacts) | `python hermes_smart_backup.py` |
| System backup only | `python hermes_smart_backup.py --backup-only` |
| Artifacts only | `python hermes_smart_backup.py --artifacts-only` |
| Preview only | `python hermes_smart_backup.py --dry-run` |
| List cloud content | `python hermes_smart_backup.py --list-cloud` |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All parts succeeded |
| 2 | One or more parts failed |

## Artifact Scan Directories (Restricted — avoid 100K+ paths)

```python
ARTIFACT_SCAN_DIRS = [
    ".config/mobileclaw/workspaces/<workspace>/workspace/",   # primary workspace
    "AppData/Local/hermes/scripts/backups/",                  # backup output
    "AppData/Local/hermes/scripts/output/",                   # skill output
    "Desktop/",      # top-level files only (max_depth=1)
    # Do NOT include Documents/ — can have 100K+ files causing timeouts
]
```

Excluded:
- `hermes-agent/` (source code, reinstallable)
- `node_modules/`, `__pycache__/`, `.git/`, `.venv/`
- `Cache/`, `GPUCache/`, all browser caches
- Desktop deeper than 1 level (avoids shortcut files)
- Files < 100B (temp scraps) and > 50MB (large media)

## File Category Mapping

```python
ARTIFACT_CATEGORIES = {
    ".py": "code/python",   ".js": "code/javascript",
    ".ts": "code/typescript",  ".md": "docs/markdown",
    ".json": "data/json",   ".csv": "data/csv",
    ".png": "images/png",   ".jpg": "images/jpg",
    ".pdf": "docs/pdf",     ".zip": "archives/zip",
    ".mp4": "video",        ".mp3": "audio",
    ".sql": "data/sql",     ".db": "data/sqlite",
    # etc. — see full dict in script
}
```

Files without a mapping go into `other/`.

## Deduplication Detail

```python
# Step 1: List cloud folder contents for the target date folder
cloud_items = cloud_list_folder(token, date_folder_id)
cloud_index = {item["name"]: item for item in cloud_items}

# Step 2: For each local file, compute SHA256
import hashlib
h = hashlib.sha256()
with open(local_path, "rb") as f:
    for chunk in iter(lambda: f.read(65536), b""):
        h.update(chunk)
local_hash = h.hexdigest()

# Step 3: Compare against cloud index
# - Same name + same hash → skip (exact duplicate)
# - Same name + different hash → upload (new version)
# - Different name + same hash → skip (content duplicate)
# - Different name + different hash → upload (new)
```

## Cron Integration

```yaml
# Scheduled daily at 17:00
cronjob:
  name: hermes-daily-backup-cloud
  schedule: "0 17 * * *"
  prompt: |
    Run full backup+artifacts pipeline:
    python "C:/Users/Administrator/AppData/Local/hermes/scripts/hermes_smart_backup.py"
  enabled_toolsets: [terminal, file]
```
