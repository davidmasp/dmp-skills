from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from rich.console import Console
from rich.table import Table

from .config import Config, Skill
from .git_ops import ensure_submodules_present


@dataclass(frozen=True)
class SkillInstallRecord:
    skill: Skill
    source: Path
    target: Path


def resolve_target_directory(config: Config, target: str | None) -> Path:
    if target is None:
        return config.default_target
    return Path(os.path.expanduser(target)).resolve()


def build_install_records(config: Config, target_dir: Path, enabled_only: bool = True) -> list[SkillInstallRecord]:
    records: list[SkillInstallRecord] = []
    for skill in config.skills:
        if enabled_only and not skill.enabled:
            continue
        source = (config.root / skill.repo).resolve()
        target = target_dir / skill.name
        records.append(SkillInstallRecord(skill=skill, source=source, target=target))
    return records


@dataclass(frozen=True)
class InstallResult:
    target_dir: Path
    submodules_created: list[str]
    submodules_skipped: list[str]
    installed: list[str]
    skipped: list[str]
    missing: list[str]


def install_skills(config: Config, target: str | None = None, force: bool = False) -> InstallResult:
    target_dir = resolve_target_directory(config, target)
    target_dir.mkdir(parents=True, exist_ok=True)

    submodule_result = ensure_submodules_present(config)
    installed: list[str] = []
    skipped: list[str] = []
    missing: list[str] = []

    for record in build_install_records(config, target_dir=target_dir, enabled_only=True):
        if not record.source.is_dir():
            missing.append(f"{record.skill.qualified_name} -> missing directory {record.source}")
            continue

        if record.target.exists() or record.target.is_symlink():
            if record.target.is_symlink() and record.target.resolve() == record.source.resolve():
                skipped.append(f"{record.skill.name} already linked")
                continue

            if not force:
                skipped.append(f"{record.skill.name} exists at {record.target}")
                continue

            if record.target.is_dir() and not record.target.is_symlink():
                raise ValueError(f"Cannot replace directory target without manual cleanup: {record.target}")
            record.target.unlink(missing_ok=True)

        record.target.symlink_to(record.source, target_is_directory=True)
        installed.append(f"{record.skill.name} -> {record.source}")

    return InstallResult(
        target_dir=target_dir,
        submodules_created=submodule_result.created,
        submodules_skipped=submodule_result.skipped,
        installed=installed,
        skipped=skipped,
        missing=missing,
    )


def render_install_summary(result: InstallResult, console: Console) -> None:
    summary = Table(title=f"Install summary: {result.target_dir}")
    summary.add_column("Status")
    summary.add_column("Details")
    for item in result.submodules_created:
        summary.add_row("submodule-added", item)
    for item in result.submodules_skipped:
        summary.add_row("submodule-skipped", item)
    for item in result.installed:
        summary.add_row("installed", item)
    for item in result.skipped:
        summary.add_row("skipped", item)
    for item in result.missing:
        summary.add_row("missing", item)
    console.print(summary)
