# Agent Skills

Git-native management for AI agent skills using submodules, TOML configuration, and symlink-based installation.

## Goals

- Track upstream skill repositories with Git submodules
- Curate a subset of skills from each repository
- Install skills as symbolic links instead of copying files
- Reproduce the same skill set across multiple machines
- Keep the toolchain minimal: `git`, `uv`, Python, Typer, Rich

## Repository Layout

```text
agent-skills/
├─ skills.toml
├─ external/
│  ├─ obsidian-skills/
│  ├─ claude-scientific-skills/
│  └─ anthropic-skills/
├─ scripts/
│  ├─ agent_skills.py
│  ├─ install_skills.py
│  ├─ uninstall_submodule.py
│  ├─ update_skill.py
│  └─ update_submodules.py
├─ src/agent_skills/
├─ pyproject.toml
└─ README.md
```

## Clone

Clone with submodules:

```bash
git clone --recurse-submodules https://github.com/<org>/agent-skills.git
cd agent-skills
```

If already cloned without submodules:

```bash
git submodule update --init --recursive
```

## Configure Skills

Edit [`skills.toml`](/Users/david.mas/projects/dmp-skills/skills.toml) to choose repositories and enable skills.

Each repository entry must define both a local `path` and its upstream `url`:

```toml
[repositories.obsidian]
path = "external/obsidian-skills"
url = "https://github.com/kepano/obsidian-skills"
```

Each skill entry defines the full source path to link, and `name` becomes the directory name under the target base:

```toml
[[skills.skill]]
name = "defuddle"
repo = "external/obsidian-skills/skills/defuddle"
enabled = true
```

## Install Skills

```bash
uv run dmp-skills install
uv run dmp-skills validate
uv run dmp-skills update-submodules
uv run dmp-skills update-skill anthropic
uv run dmp-skills uninstall-submodule obsidian
```

The original script paths remain as thin compatibility wrappers around the unified CLI:

```bash
uv run scripts/install_skills.py install
uv run scripts/uninstall_submodule.py uninstall-submodule obsidian
uv run scripts/update_submodules.py update-submodules
uv run scripts/update_skill.py update-skill anthropic
```

Install skills:

```bash
uv run dmp-skills install
```

`install` now creates any missing configured submodules before linking enabled skills. Existing submodules are left unchanged.
By default, links are created under `~/.agents/skills/<name>`.

Validate enabled skills:

```bash
uv run dmp-skills validate
```

`validate` checks each enabled skill from `skills.toml` for `SKILL.md`, required frontmatter, matching configured name, supported `agents/openai.yaml`, and generated or unexpected clutter.

Install to a custom target:

```bash
uv run dmp-skills install --target ~/.skills
```

Force replacement of conflicting targets:

```bash
uv run dmp-skills install --force
```

## Update All Submodules

```bash
uv run dmp-skills update-submodules
```

By default this skips repositories that contain excluded skills listed under `[update].exclude` in `skills.toml`.

To override that safety check:

```bash
uv run dmp-skills update-submodules --include-excluded
```

## Update One Repository

```bash
uv run dmp-skills update-skill anthropic
```

## Run Tests

```bash
uv run python -m unittest
```

This repository also supports explicit unittest discovery:

```bash
uv run python -m unittest discover -s tests
```

## Uninstall One Submodule

```bash
uv run dmp-skills uninstall-submodule obsidian
```

This deinitializes the configured submodule, removes it from the index and working tree, and deletes its cached checkout under `.git/modules/`.

## Notes

- Installation creates missing configured submodules and then performs filesystem checks and symlink creation.
- Skill contents are never copied.
- Re-running install is idempotent unless `--force` is used.
- Update operations shell out to `git submodule update --remote --merge`.
