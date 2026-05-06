---
name: justfile-builder
description: Create clean, low-complexity Justfiles from a natural-language prompt plus repository context. Use when Codex needs to author or update a `justfile` or `Justfile`, especially for summarizing scripts in folders like `scripts/`, `bin/`, or `tools/`, wrapping common developer or sysadmin tasks, standardizing repeated shell commands, or proposing a small task runner for an existing project.
---

# Justfile Builder

## Overview

Create focused `Justfile`s that expose useful project commands without turning the file into a second programming language. Prefer a small number of explicit recipes, predictable naming, clear doc comments, and portable shell commands over clever abstractions.

## Workflow

Follow this sequence:

1. Inspect the repository and identify the task surface.
2. Decide whether the `Justfile` should summarize existing scripts, expose common maintenance commands, or do both.
3. Generate a compact recipe set with stable names and minimal indirection.
4. Validate the result with `just --fmt --check` or `just --fmt`, and if possible run `just --summary` or `just --list`.

## Inspect the Project

Start by checking whether a `justfile` already exists. Update it when it is already present unless the user explicitly asks for a separate file.

Inspect likely command locations:

- `scripts/`
- `bin/`
- `tools/`

If the request is folder-driven, use `scripts/inventory_runnable_files.py` to summarize runnable files before drafting recipes:

```bash
python3 scripts/inventory_runnable_files.py .
python3 scripts/inventory_runnable_files.py . --dirs scripts bin tools
```

Use the script output to decide:

- which scripts deserve first-class recipes
- which scripts should be omitted because they are too niche or internal
- whether several scripts should instead be represented by a single higher-level recipe

## Build the Justfile

Prefer this structure:

1. Optional settings only when they solve a real problem.
2. A useful default recipe, often one that lists available commands.
3. Small public recipes with doc comments.
4. Private helper recipes only when repetition would otherwise hurt readability.

Prefer explicit commands such as:

- `uv run scripts/build.py`
- `bash scripts/deploy.sh`
- `Rscript scripts/analysis.R`
- `cargo test`

Avoid unnecessary complexity:

- Do not introduce modules, imports, unstable features, or advanced attributes unless the user clearly needs them.
- Do not create deep dependency graphs for simple projects.
- Do not hide core behavior behind shell variables or backticks when a direct command is clearer.
- Do not add recipes that merely mirror trivial one-off commands unless they improve discoverability.

When wrapping scripts with arguments, quote user-provided values safely and keep parameter usage simple.

## Recipe Selection Heuristics

For script-summary requests:

- Create one recipe per important script when the script names are already meaningful.
- Collapse very similar scripts into one parameterized recipe only if the result stays obvious.
- Add short doc comments so `just --list` is useful.

For sysadmin or machine-maintenance requests:

- Prefer safe read-only tasks first: disk usage, process listing, service status, log tailing, package updates checks.
- Put destructive actions behind explicit names like `cleanup-cache` or `restart-service`.
- Use `[confirm]` only when the task is actually risky and the user wants guardrails.
- Keep platform assumptions explicit. If the commands are macOS-only or Linux-only, say so in comments or use platform-specific recipes only when necessary.

## Output Conventions

Target a `Justfile` that is easy to scan:

- Keep public recipe names short, kebab-case, and verb-led.
- Add a doc comment above each public recipe unless the name is fully self-explanatory.
- Prefer `default:` with `@just --list` when there is no obvious default action.
- Prefer linewise recipes over shebang or script recipes unless multi-line shell state is actually required.
- Use `set shell := ["bash", "-uc"]` or similar only when the commands require shell features not guaranteed by default `sh`.
- Avoid `set dotenv-*`, `set export`, `set positional-arguments`, and unstable features unless the repository clearly benefits from them.

Read [references/justfile-patterns.md](references/justfile-patterns.md) when you need more guidance on what to include or avoid.

## Example Requests

- `Create a Justfile that summarises the scripts found in the scripts/ folder of this directory.`
- `Create a clean Justfile for this repo with recipes for lint, test, format, and run based on the existing tooling.`
- `Write a Justfile for common sysadmin tasks on this machine, keeping it compact and readable.`
- `Update the existing justfile so it lists and documents the deployment scripts under bin/.`
