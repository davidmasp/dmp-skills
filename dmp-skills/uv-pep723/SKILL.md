---
name: uv-pep723
description: Develop standalone Python scripts as uv-compatible PEP 723 files with inline dependencies, a uv run shebang, and runnable verification. Use when a coding task should produce a self-contained Python script rather than a project-managed package.
---

# UV PEP 723 Script

Develop the requested coding task as a standalone Python script that carries its own runtime metadata.

## Required file shape

Put this exact shebang on the first line:

```python
#!/usr/bin/env -S uv run --script
```

Immediately after it, add a PEP 723 metadata block. Set `requires-python` to the minimum supported Python version and list every third-party runtime dependency in `dependencies`:

```python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pandas",
#     "polars",
# ]
# ///
```

Keep imports and application code after the metadata block. Use the standard library when practical, and add only dependencies the implementation actually needs. Do not rely on a repository `pyproject.toml` to supply dependencies for this standalone script.

## Implementation guidance

- Preserve the user's requested filename, interface, arguments, and output format.
- Use normal Python packaging and CLI conventions appropriate to the task, but keep the deliverable self-contained: no local package imports unless the user explicitly wants repository coupling.
- Make the script executable when direct invocation is part of the requested workflow; the shebang is still valid when invoked through `uv run --script`.
- Avoid putting code before the shebang or inside the metadata block.

## Verification

Run the script through uv using the script mode:

```bash
uv run --script path/to/script.py [args]
```

When direct execution is expected, also verify:

```bash
./path/to/script.py [args]
```

Use the task's tests or a small synthetic fixture to verify behavior. At minimum, check that uv can parse the metadata and that the script's normal entry point starts successfully. Report separately if only static or synthetic verification was possible.
