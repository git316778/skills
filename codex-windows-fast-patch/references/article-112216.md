Article: https://www.autoxb.com/article/112216
Title: windows 解决 codex 的 computer use 插件无法使用问题

Summary of relevant guidance:
- Keep a backup before editing plugin sources.
- Create a writable plugin source under the Codex user profile.
- Register the writable `openai-bundled` source.
- Re-add `chrome@openai-bundled` and `computer-use@openai-bundled`.
- Validate with `codex plugin list --marketplace openai-bundled` and restart Codex.
