---
name: add-external-skill-repo
description: Add or explain external skill repositories in this dmp-skills repo. Use when Codex needs to configure third-party skill collections as Git submodules, update `skills.toml`, select compatible skill folders, install enabled skills as symlinks, validate external skill compatibility, or give repo-specific guidance for examples such as `mattpocock/skills`.
---

# Add External Skill Repo

## Overview

Configure third-party skill collections through this repository's Git-native workflow: declare the upstream repository in `skills.toml`, enable individual skill folders, then use the existing install and validation commands. Keep external repositories curated; do not bypass this repo's source of truth with upstream-specific installers unless the user explicitly wants that.

## Workflow

Follow this sequence:

1. Inspect `skills.toml` and existing `external/` entries to match local naming and path conventions.
2. Identify the upstream repository URL and choose a stable local path under `external/<owner>/<repo>` unless the repo already uses a different convention.
3. Add a `[repositories.<key>]` entry with `path` and `url`.
4. Inspect the upstream layout before enabling skills. Use a browser, GitHub API, `git ls-remote`, or the checked-out submodule as appropriate.
5. Add one `[[skills.skill]]` entry per skill folder that should be installed.
6. Run `uv run scripts/agent_skills.py install` or `uv run dmp-skills install` to add missing submodules and create symlinks.
7. Run `uv run scripts/agent_skills.py validate` or `uv run dmp-skills validate` and fix only repo-local configuration issues unless the user explicitly wants to patch vendored content.

## Configuration Pattern

Repository entries declare external collections:

```toml
[repositories.example]
path = "external/example-owner/example-skills"
url = "https://github.com/example-owner/example-skills.git"
```

Skill entries point to the exact skill directory and define the local install name:

```toml
[[skills.skill]]
name = "example-skill"
repo = "external/example-owner/example-skills/skills/example-skill"
enabled = true
```

The `install` command creates missing configured submodules before linking enabled skills. Existing submodules are left unchanged.

## Compatibility Checks

Enable only folders that satisfy this repo's validator:

- The configured `repo` path exists and is a directory.
- `SKILL.md` exists at the top level of the skill directory.
- `SKILL.md` starts with YAML frontmatter containing only `name` and `description`.
- The frontmatter `name` matches the configured `[[skills.skill]].name`.
- Optional agent metadata lives at `agents/openai.yaml`.
- Top-level skill entries are limited to `SKILL.md`, `agents/`, `references/`, and `scripts/`.

If an upstream collection has incompatible folders, prefer one of these approaches:

- Leave incompatible skills disabled.
- Ask whether to create a repo-local wrapper or adapted first-party skill under `dmp-skills/`.
- Avoid modifying files under `external/` unless the task explicitly asks to change vendored or submodule contents.

## Matt Pocock Example

For `mattpocock/skills`, declare the collection:

```toml
[repositories.mattpocock]
path = "external/mattpocock/skills"
url = "https://github.com/mattpocock/skills.git"
```

Then enable selected skill folders from the upstream layout. Matt's repository has used category folders under `skills/`, so entries can look like this after confirming the paths still exist:

```toml
[[skills.skill]]
name = "tdd"
repo = "external/mattpocock/skills/skills/engineering/tdd"
enabled = true

[[skills.skill]]
name = "diagnosing-bugs"
repo = "external/mattpocock/skills/skills/engineering/diagnosing-bugs"
enabled = true

[[skills.skill]]
name = "grill-me"
repo = "external/mattpocock/skills/skills/productivity/grill-me"
enabled = true
```

If the upstream README recommends a command such as `npx skills@latest add mattpocock/skills`, treat it as upstream-specific guidance. In this repo, prefer the `skills.toml` plus submodule workflow so future installs, updates, validation, and commits remain reproducible.

## Git Hygiene

Before committing, inspect the worktree and stage only the files related to the external skill change:

```bash
git status --short
git diff
git add skills.toml .gitmodules external/<owner>/<repo>
```

If `install` creates or updates a submodule, include the `.gitmodules` change and the submodule gitlink. Leave unrelated local changes alone.
