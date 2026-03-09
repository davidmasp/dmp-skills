---
name: ics-extractor
description: Extract calendar events from unstructured or semi-structured text and generate valid RFC 5545 iCalendar (.ics) files, one event per file, with event metadata and configurable reminders. Use when users ask to parse schedules, meetings, appointments, or event lists into individual calendar invite files.
---

# ICS Extractor

Convert user-provided text into one `.ics` file per event.

## Workflow

1. Parse input text into normalized event records.
2. Validate each event has required fields:
   - `summary`
   - `start` (ISO-8601 datetime)
   - either `end` or `duration_minutes`
3. Run `scripts/generate_ics.py` to generate files.
4. Return a concise list of created files and any skipped/invalid records.

## Normalize Event Records

Prefer JSON for deterministic generation.

Use this shape for each event:

```json
{
  "summary": "Project Sync",
  "start": "2026-03-02T09:00:00",
  "end": "2026-03-02T09:30:00",
  "timezone": "America/New_York",
  "location": "Zoom",
  "description": "Weekly sync",
  "alert_minutes": 5
}
```

Notes:
- `start` and `end` may also include offsets (example: `2026-03-02T09:00:00-05:00`).
- If `end` is missing, provide `duration_minutes`.
- If `alert_minutes` is missing, pass `--default-alert-minutes`.
- Keep one logical event per record.

## Generate ICS Files

Command:

```bash
python3 scripts/generate_ics.py --input events.json --out-dir out --default-alert-minutes 5
```

For key/value block input (semi-structured):

```bash
python3 scripts/generate_ics.py --input events.txt --out-dir out --default-alert-minutes 20
```

Supported key aliases in text blocks:
- `summary`, `title`, `subject`
- `start`, `starts_at`
- `end`, `ends_at`
- `duration_minutes`, `duration`
- `timezone`, `tz`
- `location`, `description`, `url`, `alert_minutes`, `uid`

Block separators:
- `---` line, or
- blank lines between key/value groups.

## Output Rules

- Emit one `.ics` file per event.
- Include `VCALENDAR` + `VEVENT` and one `VALARM` (`ACTION:DISPLAY`).
- Use RFC 5545 escaping for text fields.
- Use CRLF line endings and 75-octet line folding.
- Produce stable, filesystem-safe filenames.

## Error Handling

- Skip invalid events and report why.
- Do not stop whole batch unless all events are invalid.
- If dates are ambiguous in unstructured text, state assumptions explicitly before generating files.
