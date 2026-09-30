# Copy the delta-hmi-style skill into Claude Code's personal skills folder.
$target = Join-Path $env:USERPROFILE ".claude\skills\delta-hmi-style"
New-Item -ItemType Directory -Force $target | Out-Null
Copy-Item (Join-Path $PSScriptRoot "skills\delta-hmi-style\SKILL.md") $target -Force
Write-Host "Installed to $target"
