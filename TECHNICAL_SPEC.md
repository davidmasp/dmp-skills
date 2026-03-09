# Agent Skills Repository - Technical Specification

## Overview

This repository provides a portable, Git-based system for managing AI agent skills across multiple machines.

The system:

- Uses Git submodules to track external skill repositories, with upstream URLs stored in `skills.toml`
- Allows curated selection of skills via configuration
- Installs skills as symbolic links instead of copies
- Supports multi-machine reproducibility
- Uses Python scripts with Typer CLI, executed via `uv`
- Maintains a TOML configuration file describing installed skills

## Design Goals

### Core Goals

- Simple Git-based workflow
- Track upstream skills via submodules
- Allow partial selection of skills from each repository
- Install skills via symlinks
- Support multi-machine installation
- Avoid plugin ecosystems or external package managers

### Operational Goals

- Deterministic installations
- Easy updates from upstream skill repos
- Clear configuration format
- Minimal dependencies

## Key Decisions

- Configuration lives in [`skills.toml`](/Users/david.mas/projects/dmp-skills/skills.toml)
- Source repositories live under `external/`
- CLI entrypoints live under `scripts/` and are intended to run via `uv run`
- The primary CLI is `scripts/agent_skills.py` with Typer subcommands for install and update operations
- Shared Python code lives in [`src/agent_skills`](/Users/david.mas/projects/dmp-skills/src/agent_skills)
- Installs are symlink-based and idempotent

## Implemented Commands

```bash
uv run scripts/agent_skills.py install
uv run scripts/agent_skills.py update-submodules
uv run scripts/agent_skills.py update-skill obsidian
```
