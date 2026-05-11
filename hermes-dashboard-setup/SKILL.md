---
name: hermes-dashboard-setup
description: Set up and run Hermes Agent web dashboard - install, build frontend, launch
tags: [hermes, dashboard, web-ui, setup]
---

# Hermes Dashboard Setup

## Problem
`pip install hermes-agent[web]` installs CLI but NOT the web frontend. Running `hermes dashboard` returns "Frontend not built".

## Installation

```bash
# Install with web extras
python -m pip install hermes-agent[web]

# On Windows, if pip not in PATH:
/c/Program\ Files/Python313/python.exe -m pip install hermes-agent[web]
```

## Launch Dashboard

```bash
# CLI method (requires frontend built)
python -m hermes_cli.main dashboard --port 9120 --no-open
```

Common issues:
- Port 9119 may be in use (try `--port 9120`)
- Frontend not built → see below

## Build Frontend (Required)

The web frontend is NOT included in the pip package. Build from source:

```bash
# Clone repo
git clone --depth 1 https://github.com/NousResearch/hermes-agent.git /tmp/hermes-agent-src
cd /tmp/hermes-agent-src/web

# Install dependencies and build
npm install
npm run build

# Copy web_dist to site-packages
cp -r web_dist ~/.hermes/hermes_cli/  # or to Python site-packages
```

## Verify

```bash
# Check if frontend exists
ls ~/.hermes/hermes_cli/web_dist/

# Or in site-packages
ls /c/Program\ Files/Python313/Lib/site-packages/hermes_cli/web_dist/
```

## Fallback: Use CLI Chat

If dashboard fails, use CLI mode:
```bash
python -m hermes_cli.main chat
```

## Notes
- Dashboard runs on FastAPI + uvicorn
- Default port: 9119
- Uses session token authentication
- Web_dist path: `hermes_cli/web_dist/` relative to package location