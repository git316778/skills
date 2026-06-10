name: codex-windows-fast-patch
description: Use when the user wants to fix Windows Codex's auxiliary Computer Use, Chrome, and plugin issues.
---

# codex-windows-fast-patch
This skill guides one repair workflow for Windows Codex when Fast Mode / Computer Use / Chrome plugins appear unavailable, with bundled plugin source support.

## Use
Use this when:
- The user is on Windows and reports Codex shows Computer Use / Chrome as not available from the UI.
- The local `codex` CLI is not runnable from normal context because WindowsApps protected paths block direct execution.

## Files
- See `scripts/repair-computer-use.ps1` for the local mirror backup, marketplace repair, and restart validation commands.
