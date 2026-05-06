# Justfile Patterns

Use this reference when choosing patterns for generated `Justfile`s.

## Keep

- One clear default recipe, usually `@just --list` when no single workflow dominates.
- Short public recipe names like `test`, `lint`, `fmt`, `serve`, `logs`, `backup-db`.
- Doc comments above public recipes.
- Direct commands that mirror how a maintainer would run the task by hand.
- Light parameterization for obvious cases such as `tail service="nginx"` or `script name`.

## Avoid

- Large variable sections with computed values unless they simplify several recipes.
- `import`, `mod`, unstable features, or user-defined functions for ordinary project automation.
- Backticks, `shell(...)`, or complex string interpolation when a normal shell command is enough.
- Recipes that recursively call `just` unless there is a concrete reason.
- Over-general wrapper recipes like `run-tool TOOL *ARGS` that obscure what the project actually supports.

## Prefer Dependencies Sparingly

Use dependencies when they model a real workflow:

- `check: fmt-check lint test`
- `release: build test`

Do not introduce dependencies just to avoid repeating one command once or twice.

## Script Wrapping

When wrapping repository scripts:

- Preserve the script's normal invocation style.
- Call scripts with the interpreter they already imply when needed, for example `uv run scripts/foo.py`.
- Use `./script.sh` only when the executable bit and shebang are already part of the repo contract.
- Add recipe comments that describe intent, not the filename alone.

## Sysadmin Bias

For generic sysadmin `Justfile`s, bias toward:

- inspection
- diagnostics
- status
- logs
- backups
- safe cleanup

Treat restart, stop, delete, or prune commands as opt-in and name them explicitly.
