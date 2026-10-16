"""Export Windows Event Log entries that explain crashes, freezes and driver problems (issue #3)."""

import json
import subprocess
from pathlib import Path

OUTPUT_PATH = Path("data/raw/events.jsonl")
LOGS = ("System", "Application")

# Critical, Error, Warning.
DEFAULT_LEVELS = (1, 2, 3)

# Kept at every level, because Windows logs some of the most useful crash
# evidence as Information (e.g. Windows Error Reporting's GPU-reset reports).
# Matched by provider + ID: IDs alone collide across providers.
HIGH_VALUE = {
    "System": {
        "Microsoft-Windows-Kernel-Power": [41],               # unexpected shutdown/reboot
        "EventLog": [6008],                                   # previous shutdown was unexpected
        "Microsoft-Windows-WER-SystemErrorReporting": [1001],  # BSOD bugcheck
        "Display": [4101],                                    # display driver stopped responding
        "nvlddmkm": None,                                     # all NVIDIA driver events (13, 14, 153, ...)
    },
    "Application": {
        "Windows Error Reporting": [1001],  # crash reports: BlueScreen, LiveKernelEvent, APPCRASH...
        "Application Error": [1000],        # app crashed
        "Application Hang": [1002],         # app froze
    },
}

_SCRIPT = r"""
$ErrorActionPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$start = (Get-Date).AddDays(-__DAYS__)
$filters = ConvertFrom-Json '__FILTERS__'
$seen = @{}
$out = New-Object System.Collections.Generic.List[object]
foreach ($f in $filters) {
  $h = @{ LogName = $f.log; StartTime = $start }
  if ($f.levels) { $h.Level = [int[]]$f.levels }
  if ($f.provider) { $h.ProviderName = $f.provider }
  if ($f.ids) { $h.Id = [int[]]$f.ids }
  foreach ($e in (Get-WinEvent -FilterHashtable $h)) {
    $key = "$($e.LogName)|$($e.RecordId)"
    if ($seen.ContainsKey($key)) { continue }
    $seen[$key] = $true
    $msg = $e.Message
    if (-not $msg) { $msg = ($e.Properties | ForEach-Object { $_.Value }) -join ' | ' }
    $out.Add([ordered]@{
      timestamp = $e.TimeCreated.ToUniversalTime().ToString('o')
      log = $e.LogName
      record_id = $e.RecordId
      provider = $e.ProviderName
      event_id = $e.Id
      level = [int]$e.Level
      level_name = $e.LevelDisplayName
      message = $msg
    })
  }
}
ConvertTo-Json -InputObject $out.ToArray() -Depth 3 -Compress
"""


def build_filters(levels=DEFAULT_LEVELS) -> list[dict]:
    filters = []
    for log in LOGS:
        filters.append({"log": log, "levels": list(levels)})
        for provider, ids in HIGH_VALUE[log].items():
            filters.append({"log": log, "provider": provider, "ids": ids})
    return filters


def _as_list(value) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def read_events(days: int = 30) -> list[dict]:
    filters = json.dumps(build_filters()).replace("'", "''")
    script = _SCRIPT.replace("__DAYS__", str(int(days))).replace("__FILTERS__", filters)
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True, check=True, timeout=600,
    )
    out = result.stdout.decode("utf-8-sig").strip()
    events = _as_list(json.loads(out)) if out else []
    for e in events:
        if e.get("message"):
            e["message"] = e["message"].replace("\r\n", "\n").strip()
    events.sort(key=lambda e: e["timestamp"])
    return events


def save(events: list[dict], path: Path = OUTPUT_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return path
