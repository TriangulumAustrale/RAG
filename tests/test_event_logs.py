from rag.collect import event_logs


def test_filters_cover_levels_and_high_value_events():
    filters = event_logs.build_filters()
    assert {"log": "System", "levels": [1, 2, 3]} in filters
    assert {"log": "Application", "levels": [1, 2, 3]} in filters
    # Windows Error Reporting crash reports are Information level, so they
    # need their own filter with no level restriction.
    wer = {"log": "Application", "provider": "Windows Error Reporting", "ids": [1001]}
    assert wer in filters
    assert {"log": "System", "provider": "nvlddmkm", "ids": None} in filters


def test_save_writes_one_event_per_line(tmp_path):
    events = [{"event_id": 1, "message": "ä"}, {"event_id": 2, "message": "b"}]
    path = event_logs.save(events, tmp_path / "events.jsonl")
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2 and "ä" in lines[0]


def test_read_events_on_this_machine():
    events = event_logs.read_events(days=2)
    assert events, "expected at least one warning/error in the last 2 days"
    e = events[0]
    assert {"timestamp", "log", "record_id", "provider", "event_id", "level", "message"} <= e.keys()
    assert events == sorted(events, key=lambda e: e["timestamp"])
