#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import re
import sys
import uuid
from pathlib import Path


def fold_ical_line(line: str, limit: int = 75) -> str:
    raw = line.encode("utf-8")
    chunks = []
    while len(raw) > limit:
        split = limit
        while split > 0 and (raw[split] & 0b1100_0000) == 0b1000_0000:
            split -= 1
        if split == 0:
            split = limit
        chunks.append(raw[:split].decode("utf-8", errors="strict"))
        raw = raw[split:]
    chunks.append(raw.decode("utf-8", errors="strict"))
    return "\r\n ".join(chunks)


def esc_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def parse_iso_datetime(value: str) -> dt.datetime:
    val = value.strip()
    if val.endswith("Z"):
        return dt.datetime.fromisoformat(val.replace("Z", "+00:00"))
    return dt.datetime.fromisoformat(val)


def fmt_dtstamp(now: dt.datetime) -> str:
    return now.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def fmt_dt_field(key: str, value: dt.datetime, timezone: str | None) -> str:
    if value.tzinfo is not None:
        utc_val = value.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return f"{key}:{utc_val}"
    if timezone:
        local = value.strftime("%Y%m%dT%H%M%S")
        return f"{key};TZID={timezone}:{local}"
    local = value.strftime("%Y%m%dT%H%M%S")
    return f"{key}:{local}"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug[:80] or "event"


def normalize_event(raw: dict, default_alert: int, default_tz: str | None) -> dict:
    alias = {
        "title": "summary",
        "subject": "summary",
        "starts_at": "start",
        "ends_at": "end",
        "duration": "duration_minutes",
        "tz": "timezone",
    }

    event = {}
    for k, v in raw.items():
        key = alias.get(str(k).strip().lower(), str(k).strip().lower())
        event[key] = v

    if "summary" not in event or not str(event["summary"]).strip():
        raise ValueError("missing summary/title")
    if "start" not in event:
        raise ValueError("missing start")

    start = parse_iso_datetime(str(event["start"]))

    if "end" in event and str(event["end"]).strip():
        end = parse_iso_datetime(str(event["end"]))
    else:
        if "duration_minutes" not in event:
            raise ValueError("missing end or duration_minutes")
        mins = int(event["duration_minutes"])
        if mins <= 0:
            raise ValueError("duration_minutes must be > 0")
        end = start + dt.timedelta(minutes=mins)

    if end <= start:
        raise ValueError("end must be after start")

    alert = int(event.get("alert_minutes", default_alert))
    if alert < 0:
        raise ValueError("alert_minutes must be >= 0")

    tz = str(event.get("timezone") or default_tz or "").strip() or None

    return {
        "uid": str(event.get("uid") or f"{uuid.uuid4()}@ics-extractor"),
        "summary": str(event["summary"]).strip(),
        "start": start,
        "end": end,
        "timezone": tz,
        "location": str(event.get("location", "")).strip(),
        "description": str(event.get("description", "")).strip(),
        "url": str(event.get("url", "")).strip(),
        "alert_minutes": alert,
    }


def event_to_ics(event: dict, now: dt.datetime) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "PRODID:-//ics-extractor//EN",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{event['uid']}",
        f"DTSTAMP:{fmt_dtstamp(now)}",
        fmt_dt_field("DTSTART", event["start"], event["timezone"]),
        fmt_dt_field("DTEND", event["end"], event["timezone"]),
        f"SUMMARY:{esc_text(event['summary'])}",
    ]

    if event["location"]:
        lines.append(f"LOCATION:{esc_text(event['location'])}")
    if event["description"]:
        lines.append(f"DESCRIPTION:{esc_text(event['description'])}")
    if event["url"]:
        lines.append(f"URL:{esc_text(event['url'])}")

    lines.extend(
        [
            "BEGIN:VALARM",
            f"TRIGGER:-PT{event['alert_minutes']}M",
            "ACTION:DISPLAY",
            f"DESCRIPTION:{esc_text('Reminder: ' + event['summary'])}",
            "END:VALARM",
            "END:VEVENT",
            "END:VCALENDAR",
        ]
    )

    return "\r\n".join(fold_ical_line(line) for line in lines) + "\r\n"


def parse_kv_blocks(text: str) -> list[dict]:
    blocks = []
    current = []

    for line in text.splitlines():
        if line.strip() == "---":
            if current:
                blocks.append(current)
                current = []
            continue
        if not line.strip():
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(line)

    if current:
        blocks.append(current)

    events = []
    for block in blocks:
        ev = {}
        for line in block:
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            ev[k.strip()] = v.strip()
        if ev:
            events.append(ev)
    return events


def load_events(path: Path) -> list[dict]:
    data = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        parsed = json.loads(data)
        if isinstance(parsed, dict):
            if "events" in parsed and isinstance(parsed["events"], list):
                return parsed["events"]
            return [parsed]
        if isinstance(parsed, list):
            return parsed
        raise ValueError("JSON input must be an object, list, or {\"events\": [...]}.")
    return parse_kv_blocks(data)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate one RFC 5545 ICS file per event from JSON or key/value input."
    )
    parser.add_argument("--input", required=True, help="Input file (.json or text key/value blocks)")
    parser.add_argument("--out-dir", required=True, help="Output directory for .ics files")
    parser.add_argument("--default-alert-minutes", type=int, default=5)
    parser.add_argument("--default-timezone", default=None)

    args = parser.parse_args()

    in_path = Path(args.input)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        raw_events = load_events(in_path)
    except Exception as exc:
        print(f"Failed to parse input: {exc}", file=sys.stderr)
        return 1

    if not raw_events:
        print("No events found in input.", file=sys.stderr)
        return 1

    now = dt.datetime.now(dt.timezone.utc)
    failures = []
    written = []

    for idx, raw in enumerate(raw_events, start=1):
        try:
            event = normalize_event(raw, args.default_alert_minutes, args.default_timezone)
            start_stamp = event["start"].strftime("%Y%m%dT%H%M%S")
            filename = f"{idx:03d}-{start_stamp}-{slugify(event['summary'])}.ics"
            out_path = out_dir / filename
            out_path.write_text(event_to_ics(event, now), encoding="utf-8", newline="")
            written.append(str(out_path))
        except Exception as exc:
            failures.append(f"event #{idx}: {exc}")

    for path in written:
        print(path)

    if failures:
        print("Skipped invalid events:", file=sys.stderr)
        for item in failures:
            print(f"  - {item}", file=sys.stderr)

    return 0 if written else 1


if __name__ == "__main__":
    raise SystemExit(main())
