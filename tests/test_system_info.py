from datetime import datetime, timezone

from rag.collect import system_info


def test_parse_nvidia_smi():
    out = "NVIDIA GeForce RTX 2060 SUPER, 610.88, 46, 8192\n"
    assert system_info.parse_nvidia_smi(out) == [{
        "name": "NVIDIA GeForce RTX 2060 SUPER",
        "driver_version": "610.88",
        "temperature_c": 46,
        "memory_total_mb": 8192,
    }]


def test_parse_nvidia_smi_handles_unsupported_values():
    out = "Some GPU, 1.0, [N/A], 4096\n"
    assert system_info.parse_nvidia_smi(out)[0]["temperature_c"] is None


def test_as_list_wraps_single_item():
    assert system_info._as_list({"name": "x"}) == [{"name": "x"}]
    assert system_info._as_list([1, 2]) == [1, 2]
    assert system_info._as_list(None) == []


def test_uptime_hours_accepts_dotnet_timestamps():
    # .NET's "o" format uses 7 fractional digits.
    now = datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc)
    assert system_info.uptime_hours("2026-10-15T09:30:00.1234567Z", now) == 2.5


def test_collect_on_this_machine():
    info = system_info.collect()
    assert info["os"]["build"]
    assert info["cpus"] and info["gpus"]
    assert info["os"]["ram_gb"] > 0
