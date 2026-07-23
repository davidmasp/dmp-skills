# Agent Instructions

## Repository Purpose

This repository manages AI agent skills with a Git-native workflow. It curates local and external skills in `skills.toml`, installs enabled skills as symlinks, and provides a small Python CLI for install, update, uninstall, and validation workflows.

## Layout

- `skills.toml`: source of truth for repositories, enabled skills, optional machine-specific install targets, and update exclusions.
- `dmp-skills/`: first-party skills maintained in this repo.
- `external/`: vendored or submodule-backed external skill repositories.
- `src/agent_skills/`: Python package for the management CLI.
- `scripts/`: compatibility wrappers around the unified CLI.
- `tests/`: unittest coverage for config, install, and validation behavior.

## Skill Structure

Before creating or changing a skill, check the global skill creator instructions if they exist:

```text
~/.codex/skills/.system/skill-creator/SKILL.md
```

Treat that file as the current source of truth for skill anatomy and validation expectations.

Each skill directory should be self-contained and use this shape:

```text
skill-name/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── scripts/
├── references/
└── assets/
```

Only `SKILL.md` is required. Add `scripts/`, `references/`, and `assets/` only when they are useful.

Keep `SKILL.md` concise and procedural. Put long API docs, schemas, examples, and detailed domain notes in one-hop files under `references/`. Put deterministic or frequently repeated logic in `scripts/`. Put templates, icons, fonts, and other reusable output material in `assets/`.

Do not add extra human-facing documentation inside individual skill folders unless the agent must load it to perform the skill. Avoid `README.md`, changelogs, quick references, and installation guides inside skills.

## Skill Metadata

Use lowercase hyphenated skill names, and make the skill folder name match the `name` in `SKILL.md`.

`SKILL.md` frontmatter should contain only:

```yaml
---
name: skill-name
description: Clear trigger description explaining what the skill does and when to use it.
---
```

`description` is the trigger surface, so include the usage contexts there rather than in a "when to use" section in the body.

Keep `agents/openai.yaml` aligned with the skill:

```yaml
interface:
  display_name: "Human Name"
  short_description: "Short user-facing summary"
  default_prompt: "Use $skill-name to ..."
```

## Installation Configuration

The global install target remains optional and defaults to `~/.agents/skills`:

```toml
[installation]
default_target = "~/.agents/skills"
```

Define named machine profiles only when a machine needs a different target base:

```toml
[machines.work]
default_target = "~/work/agent-skills"
```

Add a per-skill override only when that skill needs a different target on a selected machine:

```toml
[[skills.skill]]
name = "example-skill"
repo = "dmp-skills/example-skill"
enabled = true
install_targets = { work = "~/work/example-project/skills" }
```

Configured paths are target bases; installation appends the skill name. Resolve targets in this order:

1. Explicit `--target`
2. The skill's `install_targets[<machine>]`
3. `[machines.<machine>].default_target`
4. `[installation].default_target`

Keep machine profiles and per-skill overrides optional so existing configurations retain their current behavior. Reject references to unknown machines rather than silently falling back.

## Development Commands

Install enabled skills:

```bash
uv run scripts/agent_skills.py install
```

Install enabled skills for a named machine profile:

```bash
uv run scripts/agent_skills.py install --machine work
```

Validate enabled skills:

```bash
uv run scripts/agent_skills.py validate
```

Run tests:

```bash
uv run python -m unittest discover -s tests
```

Update all selected submodules:

```bash
uv run scripts/agent_skills.py update-submodules
```

Update one configured repository:

```bash
uv run scripts/agent_skills.py update-skill obsidian
```

Uninstall one configured submodule:

```bash
uv run scripts/agent_skills.py uninstall-submodule obsidian
```

## Coding Guidelines

Prefer small, focused changes that match the existing Typer-based CLI and unittest style. Avoid broad refactors unless the request requires them.

Use structured parsing for TOML, YAML-like skill metadata, and filesystem paths rather than ad hoc string manipulation when practical.

Do not modify submodule contents under `external/` unless the task explicitly asks for changes there.

Do not commit generated caches or local artifacts such as `.DS_Store`, `__pycache__/`, `.venv/`, or build outputs.

## Git Workflow

Before committing, check the worktree:

```bash
git status --short
```

Review the diff and stage only files that belong to the requested change:

```bash
git diff
git add <paths>
```

Run the relevant validation before committing. For most repo changes, use:

```bash
uv run python -m unittest discover -s tests
uv run scripts/agent_skills.py validate
```

Use a concise imperative commit subject. Include a body when it helps explain why the change was made.

Always include the Codex co-author trailer in commit messages:

```text
Co-authored-by: Codex <codex@openai.com>
```

Example:

```text
Add skill validation command

Validate enabled skill metadata and resource layout from skills.toml.

Co-authored-by: Codex <codex@openai.com>
```

Never stage or commit unrelated user changes. If unrelated changes are present, leave them alone and mention them in the final response.
