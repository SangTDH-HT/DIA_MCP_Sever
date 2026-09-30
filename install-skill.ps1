# Copy the Delta skills (delta-hmi-style, diascreen) into Claude Code's personal skills folder.
foreach ($name in "delta-hmi-style", "diascreen") {
    $target = Join-Path $env:USERPROFILE ".claude\skills\$name"
    New-Item -ItemType Directory -Force $target | Out-Null
    Copy-Item (Join-Path $PSScriptRoot "skills\$name\*") $target -Recurse -Force
    Write-Host "Installed $name to $target"
}
