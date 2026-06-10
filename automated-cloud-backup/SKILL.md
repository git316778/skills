---
name: automated-cloud-backup
description: "Automated system backup to cloud storage. Periodic (cron) or on-demand full backup of agent configuration/state with cloud upload. Covers backup exclusion strategy, token persistence, and cron job setup."
triggers:
  - backup
  - 云盘自动备份
  - scheduled backup
  - 自动备份
  - backup to cloud
  - cloud backup cron
---

# Automated Cloud Backup

End-to-end pattern: backup agent state → compress → upload to cloud → keep N latest → cron triggers daily.

## What to Back Up vs What to Exclude

**Principle**: backup only what cannot be reinstalled from scratch.

| Include (user data/state) | Exclude (reinstallable source/binary) |
|---|---|
| Config files (`.env`, `config.yaml`, `SOUL.md`) | Source code directories (e.g. `hermes-agent/` source tree) |
| Skills (custom modifications) | `node_modules/`, build artifacts, dist/ |
| Session database (`state.db`) | Cache dirs (`Cache`, `Code Cache`, `audio_cache`, `image_cache`) |
| Memory files | Executables (`.exe`, `.dll`, `.msi`, `.so`) |
| Cron job definitions | `__pycache__/`, `.git/` |
| Cloud workspace scripts/skills | Large JSON caches (> 5 MB, auto-regenerated) |

### Hermes (Windows) directory map

- `C:\\Users\\<user>\\AppData\\Local\\hermes\\` — primary config/skills/sessions
- `C:\\Users\\<user>\\AppData\\Local\\hermes\\hermes-agent\\` — source code (exclude entirely)
- `C:\\Users\\<user>\\AppData\\Roaming\\Hermes\\` — Electron app state (only keep Preferences, Local State, Dictionaries)
- `C:\\Users\\<user>\\.config\\mobileclaw\\` — mobileclaw workspace

> **Critical**: the `hermes-agent/` directory contains the full source tree with 100K+ files. `os.walk` through it takes 15+ seconds and produces a 100+ MB zip. Always skip it.

## Performance: Avoid Large Source Tree Walks

```python
# BAD: walks everything including 100K source files — may hang > 120s
for root, dirs, files in os.walk(src_dir):
    ...

# GOOD: skip reinstallable directories before recursing
SKIP_DIRS = {"hermes-agent", "node_modules", "dist", "release", ".git", "__pycache__"}
for root, dirs, files in os.walk(src_dir):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
```

## Zip Duplicate-Name Warning

When `os.walk` yields the same file twice (e.g. root listing + explicit state.db), `ZipFile.write` emits `UserWarning: Duplicate name`.

**Fix**: track already-included files:

```python
included_elsewhere = {"state.db"}  # handled separately
for fname in os.listdir(dir_path):
    if fname in included_elsewhere:
        continue
    zf.write(os.path.join(dir_path, fname), arcname)
```

## Token Persistence

Save cloud-storage API tokens in a `.env` file next to the backup script:

```env
YUN139_TOKEN=*** in scripts:

```python
import os
token = os.environ.get("YUN139_TOKEN", "").strip()
if not token:
    token_file = os.path.join(os.path.dirname(__file__), "yun139_token.env")
    with open(token_file) as f:
        for line in f:
            if line.startswith("YUN139_TOKEN=***            token = line.split("=", 1)[1].strip()
```

**Security**: always add `.env` files to `.gitignore`.

## Token Refresh for Long-Running Jobs

139-cloud tokens expire. Before uploading, refresh if valid-for < 15 days:

```python
session = Yun139Session(token)
ok, result = session.refresh_token()
if ok and result.get("token") != token:
    # persist new token to yun139_token.env
```

## Cron Job Setup (Hermes)

```
cronjob: create
  name: system-daily-backup
  schedule: "0 17 * * *"    # every day 17:00
  enabled_toolsets: ["terminal", "file"]
  prompt: run backup script, report result
```

## File Cleanup

Auto-remove old backups, keeping only the N most recent:

```python
BACKUP_DIR = "backups/"
KEEP = 5
files = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith(".zip")], reverse=True)
for old in files[KEEP:]:
    os.remove(os.path.join(BACKUP_DIR, old))
```

## Cloud Upload Target Pattern

For 139-cloud, the AI空间 folder ID is a known constant that avoids a round-trip list query:

```python
AI_SPACE_FOLDER_ID = "FgqAR0GH6rLhqrVtw9FBJxpfwQV-z-r04"
upload_mgr.upload_file(
    os.path.basename(local_path), local_path,
    AI_SPACE_FOLDER_ID,
    progress_callback=lambda p: print(f"\\r{p}%", end="", flush=True)
)
```

## Full Pipeline Sketch

```python
# 1. Package
zip_path = make_backup(EXCLUDE_DIRS)            # ~4 MB, ~15s

# 2. Load + refresh token
token = get_token()
session = Yun139Session(token)
session.refresh_token()

# 3. Upload
AI_SPACE = "FgqAR0GH6rLhqrVtw9FBJxpfwQV-z-r04"
upload_mgr = Yun139UploadManager(session)
ok, data = upload_mgr.upload_file(basename, zip_path, AI_SPACE, progress_callback=progress)

# 4. Cleanup
clean_old_backups(keep=5)
```

## Cloud Upload Deduplication (New Pattern)

Before uploading any file, build a cloud index to avoid re-uploading identical content:

```python
def build_cloud_index(token, folder_id):
    """返回 {name: {fileId, size, contentHash}} 用于去重"""
    items = cloud_list_folder(token, folder_id)
    idx = {}
    for item in items:
        if item["type"] == "file":
            idx[item["name"]] = {
                "fileId": item.get("fileId"),
                "size": item.get("size", 0),
                "hash": item.get("contentHash"),
            }
    return idx


def is_duplicate(local_path, local_size, local_hash, cloud_index):
    """
    检查本地文件是否已在云盘存在
    返回 (is_dup, reason): hash_match/name_size_match/hash_only_match/new
    """
    basename = os.path.basename(local_path)
    if basename in cloud_index:
        info = cloud_index[basename]
        if info["hash"] == local_hash:
            return True, "hash_match"
        if info["size"] == local_size:
            return True, "name_size_match"
        return False, "name_diff"  # 同名不同内容
    for name, info in cloud_index.items():
        if info["hash"] == local_hash:
            return True, "hash_only_match"  # 不同名但内容相同
    return False, "new"
```

## Artifacts Organization Pattern

Daily conversation artifacts organized by date:

```
AI空间/
├── hermes_backup/                    # 系统全量备份（zip）
│   └── hermes_backup_YYYYMMDD_HHMMSS.zip
└── hermes_artifacts/
    └── YYYY-MM-DD/                   # 当天产物
        ├── code/
        ├── docs/
        ├── images/
        ├── audio/
        ├── video/
        ├── data/
        └── other/
```

Upload flow:
1. `cloud_create_folder(parent, "hermes_artifacts")` → get folder_id
2. `cloud_create_folder(artifacts_id, "YYYY-MM-DD")` → get date folder_id
3. `build_cloud_index(token, date_folder_id)`
4. Scan local artifact dirs (restricted: workspace, Desktop top-level, Documents)
5. For each file: categorize by extension → subfolder → dedupe check → upload

See `references/artifact-backup.md` for full implementation.

## Dry-Run Mode

Backup scripts support `--dry-run` flag to preview without uploading:

```bash
python hermes_smart_backup.py --dry-run
```

Outputs list of files that would be uploaded, with sizes and categories. Useful for verification before real runs.

## Tool Pitfall: write_file Asterisk Escaping

`write_file` auto-escapes `***` → `*` (treats as markdown emphasis). When writing Python source containing `***` separators/comments, use:

```python
# In Python string: use concatenation to avoid the trigger
SEP = "**" + "*" + " DOCSTRING " + "**" + "*"
# Or write via terminal + python -c instead
```

This affects any code generation with markdown-style `***` horizontal rules or multi-asterisk patterns.
