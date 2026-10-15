---
name: remindctl
description: Manage Apple Reminders through the remindctl CLI, using the user's existing lists and routing conventions. Use for creating, finding, editing, completing, or deleting reminders, and transferring Obsidian tasks, papers, or 3D printing notes into Reminders.
---

# Apple Reminders with remindctl

Use the installed `remindctl` CLI. Read [references/commands.md](references/commands.md) for command examples, date and alarm behavior, recurrence, and recovery from partial saves. Check the installed command's `--help` when an option is uncertain.

## Unsupported Reminders features

The installed `remindctl` version does not support reading or managing list sections, nested subtasks, or reminder tags. If the user asks to inspect or change any of these, say this CLI cannot do it and direct them to Reminders.app. Do not imply these features were checked or successfully changed, or imitate them by moving data into titles or notes.

## Access and execution

- Check `remindctl status --json` before accessing Reminders. If unavailable or unauthorized, use `remindctl doctor --for-agent` to diagnose and explain the required access step; do not repeatedly retry failing operations. `remindctl authorize` requests macOS access when setup is part of the user's request.
- Apparent lack of access in the current session can come from the sandbox blocking calls to Reminders.app even when macOS permission is granted. If that seems likely, request an elevated retry of `remindctl status --json` through the execution tool's user-approval flow before concluding that Reminders access is missing.
- The local Codex configuration already includes `remindctl` among accepted commands, so access should normally work. The persistent fix for a missing command approval is to add an allow rule for the `remindctl` command prefix in Codex's configuration (`~/.codex/rules/default.rules` on this machine).
- Prefer `--json` for reads and mutation results. Resolve current list names and IDs with `remindctl list --json`; use `--list-id` when names are ambiguous. Never invent or persist example IDs.
- Always specify the chosen list when adding a reminder. Use stable reminder IDs or unambiguous ID prefixes from current results for edits, completion, and deletion; numeric indexes depend on the current default view.
- Make the changes the user requested, then inspect the affected reminders with `remindctl info <id> --json`. Report the actual list, title, due date, and recurrence when relevant, plus any unresolved failures.

## Personal list structure

Honor an explicitly requested existing list. Otherwise infer the list from the reminder's purpose using this table. **Never create new lists. If uncertain, use Inbox.** Preserve the spelling and capitalization below when resolving names.

| List | Purpose |
| --- | --- |
| Codes | Hotel reservations and flight booking or confirmation codes. |
| Groceries | Grocery shopping. |
| House | Household chores, mostly recurring. |
| Inbox | Urgent or miscellaneous reminders, and anything whose destination is unclear. |
| Money | Personal finances, mostly recurring. |
| People | Interactions with other people and personal follow-ups. |
| Reading | Books the user wants to read. |
| Sport | Gym, exercise, and related activities. |
| Work | Research work and tasks synced from Obsidian. |
| Work Reading | Scientific papers the user wants to read. |
| printing | 3D printing projects and items. |
| sysadmin | Recurring reminders for managing the user's digital life. |

For overlaps, use the specific subject: a research collaborator follow-up belongs in Work, a paper to read in Work Reading, and a book in Reading. Use Inbox for an urgent miscellaneous item without a clearer destination. Do not assume recurrence merely because a list usually contains recurring reminders; use the requested or source-specified schedule. If a needed list is missing, fall back to an existing Inbox and report that choice. If Inbox is also unavailable or ambiguous, resolve the destination with the user instead of creating a list.

## Obsidian transfers

Read the actual source note or tasks using the available Obsidian skill or supplied content before transferring them. Use structured properties such as `title` and `url` when present; otherwise use the note's title and relevant source link. A paper or model URL means the external source URL, rather than a vault file path or Obsidian deep link. If several links could be the source, resolve which is correct; do not invent a URL. If the required URL cannot be found, report the missing information before creating an incomplete transfer.

- **Tasks → Work:** When syncing Obsidian tasks to Reminders, use Work unless the user explicitly chooses another existing list. If the source note identifies a subarea with a code, prefix the reminder title with `[CODE] - ` and then the task text. For example, a task under `ADM - Administration` titled `send invoices to Bob` becomes `[ADM] - send invoices to Bob`. Preserve explicit dates and recurrence. Do not guess a subarea code if the note does not identify one.
- **Papers → Work Reading:** Match the Obsidian note title exactly, following the user's `Author Journal Year` convention. Store the paper's URL with `--url`. If the title does not follow the convention and the necessary metadata is absent, resolve it with the user instead of inventing author, journal, or year.
- **3D printing notes → printing:** Use the note title as the reminder title and store the correct model or project URL in the native URL field with `--url`.

For repeat transfers or syncs, search the destination list by source URL or title first, including completed reminders when determining whether a note was already transferred. Inspect matches before deciding to skip or update; do not create a duplicate or reopen completed work merely because sync ran again. Treat sync as transferring the requested items; changes to Obsidian source tasks require the user's instruction.

## Change semantics

- Set due dates, notification alarms, priority, and recurrence from the request or source. A due date and an alarm are separate fields; preserve existing fields that the requested edit does not address.
- For a requested notification, set `--alarm` explicitly. It cannot enable Reminders.app's native Urgent toggle. If that toggle is specifically requested, explain the limitation and the app handoff.
- Inspect the target before changing a recurring reminder so its existing schedule is preserved unless the user requests a change.
- Complete or delete only the identified reminders within the requested scope. For bulk completion or deletion, inspect `--dry-run --json` results before execution. Use deletion's `--force` only after the targets are resolved and the deletion is already authorized; it bypasses the CLI prompt.
- If a write reports `Reminder is missing a calendar`, it may already have saved. Inspect Reminders.app or search and inspect the affected item before any retry. If its state cannot be established, stop and report the uncertainty to avoid duplicate changes.
