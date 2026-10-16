"""Snapshot of the machine's hardware and software (issue #2)."""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OUTPUT_PATH = Path("data/raw/system_info.json")

# Dates are converted to ISO strings in PowerShell, because ConvertTo-Json
# would otherwise emit them as "/Date(ms)/".
_CIM_SCRIPT = r"""
$os = Get-CimInstance Win32_OperatingSystem
$cpu = Get-CimInstance Win32_Processor
$gpu = Get-CimInstance Win32_VideoController
@{
  os = @{
    name = $os.Caption
    version = $os.Version
    build = $os.BuildNumber
    architecture = $os.OSArchitecture
    last_boot = $os.LastBootUpTime.ToUniversalTime().ToString('o')
    ram_gb = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
  }
  cpus = @($cpu | ForEach-Object { @{
    name = $_.Name.Trim()
    cores = $_.NumberOfCores
    threads = $_.NumberOfLogicalProcessors
  } })
  gpus = @($gpu | ForEach-Object { @{
    name = $_.Name
    driver_version = $_.DriverVersion
    driver_date = if ($_.DriverDate) { $_.DriverDate.ToString('yyyy-MM-dd') } else { $null }
  } })
} | ConvertTo-Json -Depth 4 -Compress
"""

_NVIDIA_FIELDS = ["name", "driver_version", "temperature_c", "memory_total_mb"]


def _run(cmd: list[str]) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60).stdout


def _as_list(value) -> list:
    # PowerShell 5.1 unwraps single-item arrays when converting to JSON.
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def read_cim() -> dict:
    out = _run(["powershell", "-NoProfile", "-NonInteractive", "-Command", _CIM_SCRIPT])
    data = json.loads(out)
    data["cpus"] = _as_list(data.get("cpus"))
    data["gpus"] = _as_list(data.get("gpus"))
    return data


def parse_nvidia_smi(output: str) -> list[dict]:
    gpus = []
    for line in output.strip().splitlines():
        values = [v.strip() for v in line.split(",")]
        if len(values) != len(_NVIDIA_FIELDS):
            continue
        gpu = dict(zip(_NVIDIA_FIELDS, values))
        for key in ("temperature_c", "memory_total_mb"):
            try:
                gpu[key] = int(gpu[key])
            except ValueError:
                gpu[key] = None
        gpus.append(gpu)
    return gpus


def read_nvidia() -> list[dict] | None:
    """NVIDIA-specific details, or None if nvidia-smi isn't available."""
    try:
        out = _run([
            "nvidia-smi",
            "--query-gpu=name,driver_version,temperature.gpu,memory.total",
            "--format=csv,noheader,nounits",
        ])
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    return parse_nvidia_smi(out)


def uptime_hours(last_boot_iso: str, now: datetime) -> float:
    last_boot = datetime.fromisoformat(last_boot_iso)
    return round((now - last_boot).total_seconds() / 3600, 1)


def collect() -> dict:
    now = datetime.now(timezone.utc)
    info = read_cim()
    info["os"]["uptime_hours"] = uptime_hours(info["os"]["last_boot"], now)
    info["nvidia"] = read_nvidia()
    info["collected_at"] = now.isoformat()
    return info


def save(info: dict, path: Path = OUTPUT_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(info, indent=2), encoding="utf-8")
    return path
