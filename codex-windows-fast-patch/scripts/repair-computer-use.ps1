: '
Skill-based repair script for Windows Codex Computer Use / marketplace issues.
Run this from an elevated PowerShell if repo-style WindowsApps folders are protected.

Backup ----------------------------------------
$ErrorActionPreference = 'SilentlyContinue'
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backup = Join-Path $HOME ".codex\backups\plugin-repair-$timestamp"
New-Item -ItemType Directory -Force $backup | Out-Null
Copy-Item (Join-Path $HOME '.codex\config.toml') $backup -Force
Copy-Item (Join-Path $HOME '.codex.codex-global-state.json') $backup -Force

Paths ----------------------------------------
$appPkg = 'C:\Program Files\WindowsApps\OpenAI.Codex_26.602.9276.0_x64__2p2nqsd0c76g0'
$src = Join-Path $appPkg 'app\resources\plugins\openai-bundled'
$dst = Join-Path $HOME '.codex\plugins\sources\openai-bundled-fixed'

Copy plugin source ---------------------------
if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
New-Item -ItemType Directory -Force $dst | Out-Null
$queue = [System.Collections.Generic.Queue[string]]::new()
$queue.Enqueue($src)
while ($queue.Count -gt 0) {
  $current = $queue.Dequeue()
  $rel = $current.Substring($src.Length).TrimStart('\')
  $target = if ($rel -eq '') { $dst } else { Join-Path $dst $rel }
  New-Item -ItemType Directory -Force $target | Out-Null
  foreach ($file in Get-ChildItem -LiteralPath $current -File -Force) {
    $out = Join-Path $target $file.Name
    [IO.File]::WriteAllBytes($out, [IO.File]::ReadAllBytes($file.FullName))
  }
  foreach ($dir in Get-ChildItem -LiteralPath $current -Directory -Force) {
    $queue.Enqueue($dir.FullName)
  }
}

Marketplace and plugin commands ----------------
Write-Output 'Next steps:'
Write-Output "- codex plugin marketplace remove openai-bundled"
Write-Output "- codex plugin marketplace add '$dst'"
Write-Output "- codex plugin add chrome@openai-bundled"
Write-Output "- codex plugin add computer-use@openai-bundled"
Write-Output '- Run: codex plugin list --marketplace openai-bundled'
Write-Output '- Restart Codex after that.'
