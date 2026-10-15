# remindctl command reference

Source: [official commands](https://remindctl.sh/commands.html), supplied by the user; syntax checked against installed remindctl 0.3.8. Check `<command> --help` for version-specific options. Examples with IDs or URLs use placeholders; replace them with resolved values.

## Unsupported features in installed 0.3.8

This CLI cannot inspect or manage list sections, nested subtasks, or Reminders tags. Its list and reminder output does not expose section or parent/child structure, and its commands do not provide tag operations. If asked for any of these, explain the limitation and direct the user to Reminders.app; never claim success or substitute titles/notes for the missing feature.

## Find and inspect

```sh
remindctl status --json
remindctl doctor --for-agent
remindctl list --json
remindctl today --json
remindctl show overdue --list Work --json
remindctl list Work "Work Reading" --json
remindctl search "invoice" --list Money --json
remindctl search "https://example.org/paper" --list "Work Reading" --completed --json
remindctl info <reminder-id> --json
```

Views include `today`, `tomorrow`, `week`, `overdue`, `upcoming`, `open`, `completed`, `all`, and a date such as `2026-10-16`. `week` covers incomplete reminders in the current calendar week, excluding the start of the next week. `search` matches titles, notes, and URLs; `--completed` includes completed reminders in addition to incomplete ones.

List names resolve by exact, case-insensitive, then normalized matches ignoring emoji and punctuation. Resolve ambiguity with `--list-id <list-id>`; the same selector works for scoped reads and reminder creation or moves. Do not use list creation, renaming, or deletion as part of routing reminders.

## Create

```sh
remindctl add "Buy milk" --list Groceries --json
remindctl add "Review analysis" --list Work --due tomorrow --json
remindctl add "Clean filters" --list House --due "2026-10-17 09:00" --repeat monthly --json
remindctl add --title "Author Journal Year" --list "Work Reading" --url "https://example.org/paper" --json
remindctl add --title "Model note title" --list printing --url "https://example.org/model" --json
```

Useful options:

| Option | Meaning |
| --- | --- |
| `--list <name>` / `--list-id <id>` | Existing destination list. Always specify one. |
| `--due <date>` | Due date, independently of notification alarms. |
| `--alarm <date>` | Notification date and time; does not enable native Urgent. |
| `--notes <text>` | Reminder notes. |
| `--url <url>` | Native EventKit URL, also mirrored into managed notes for visibility in Reminders.app. |
| `--repeat <rule>` | `daily`, `weekly`, `biweekly`, `monthly`, `yearly`, or `every N days/weeks/months/years`. |
| `--priority <value>` | `none`, `low`, `medium`, `high`. |
| `--location <address>` | Arriving geofence; `--leaving` switches to departure, `--radius <meters>` sets radius. |

Use quoted arguments or `--title` for arbitrary titles. For a positional title starting with a hyphen, put `--` immediately before the title and after all options:

```sh
remindctl add --list Inbox --json -- "--help"
```

Due dates and alarms accept relative dates, `YYYY-MM-DD`, local date-times, and ISO 8601 timestamps with explicit offsets. Prefer unambiguous ISO dates; resolve ambiguous numeric dates using the user's context. Legacy slash dates use `MM/dd/yyyy`, while day-first hyphen dates use `dd-MM-yy` or `dd-MM-yyyy`. Resolve relative expressions against the user's current local date and timezone.

## Edit, complete, delete

```sh
remindctl edit <reminder-id> --due "2026-10-18 09:00" --json
remindctl edit <reminder-id> --alarm "2026-10-18 08:55" --json
remindctl edit <reminder-id> --list Work --json
remindctl edit <reminder-id> --url "https://example.org/paper" --json
remindctl edit <reminder-id> --clear-due --json
remindctl edit <reminder-id> --clear-alarm --json
remindctl edit <reminder-id> --no-repeat --json
remindctl complete <reminder-id> --dry-run --json
remindctl complete <reminder-id> --json
remindctl delete <reminder-id> --dry-run --json
remindctl delete <reminder-id> --force --json
```

`edit` also supports `--title`, `--notes`, `--priority`, `--repeat`, `--clear-url`, `--complete`, and `--incomplete`. Changing or clearing only a due date leaves alarms unchanged. Explicit absolute alarm edits preserve relative and location alarms. Preserve authored notes when editing; let `--url` manage its own mirrored URL line.

IDs must identify one reminder. `edit`, `complete`, and `delete` also accept positive indexes from the current default listing, but indexes can change between calls. Prefer IDs. Complete/delete deduplicate repeated targets, but every supplied target must still be valid and unambiguous.

If add, edit, or complete reports `Reminder is missing a calendar`, EventKit may have saved the change despite the error. Inspect actual state before retrying; stop if the result cannot be established.

## Export and handoff

```sh
remindctl export --list Work --json
remindctl export --list Work --export-format csv
remindctl link <reminder-id>
remindctl open <reminder-id>
remindctl open --list Work --app
```

`open --list Work` without `--app` displays incomplete reminders; add `--app` for Reminders.app. Use `--plain` for stable tab-separated output, `--format table` for a human-readable table, and `--no-input` to disable interactive prompts. `--no-input` does not authorize mutations or replace deletion's `--force`.
