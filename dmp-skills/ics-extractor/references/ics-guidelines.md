# iCalendar Notes

Use RFC 5545-compatible structure:
- `BEGIN:VCALENDAR` / `END:VCALENDAR`
- `VERSION:2.0`
- `PRODID`
- `CALSCALE:GREGORIAN`
- One `VEVENT` per file

Recommended VEVENT fields:
- `UID` (globally unique)
- `DTSTAMP` (UTC)
- `DTSTART`
- `DTEND`
- `SUMMARY`

Reminder block:
- `BEGIN:VALARM`
- `TRIGGER:-PT{N}M`
- `ACTION:DISPLAY`
- `DESCRIPTION`
- `END:VALARM`

Formatting rules:
- Escape text values for `\\`, `;`, `,`, and newlines (`\\n`).
- Use CRLF line endings in output.
- Fold long content lines at 75 octets with continuation line starting with a single space.
