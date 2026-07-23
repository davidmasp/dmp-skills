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


def resolve_target_directory(
    config: Config,
    target: str | None,
    machine: str | None = None,
    skill: Skill | None = None,
) -> Path:
    if target is not None:
        return Path(os.path.expanduser(target)).resolve()
    if machine is None:
        return config.default_target

    try:
        machine_config = config.machines[machine]
    except KeyError as exc:
        raise ValueError(f"Unknown machine '{machine}' in configuration") from exc

    if skill is not None and machine in skill.install_targets:
        return skill.install_targets[machine]
    if machine_config.default_target is not None:
        return machine_config.default_target
    return config.default_target


def build_install_records(
    config: Config,
    target_dir: Path | None = None,
    enabled_only: bool = True,
    *,
    target: str | None = None,
    machine: str | None = None,
) -> list[SkillInstallRecord]:
    if target_dir is not None and target is not None:
        raise ValueError("Specify either target_dir or target, not both")

    records: list[SkillInstallRecord] = []
    for skill in config.skills:
        if enabled_only and not skill.enabled:
            continue
        source = (config.root / skill.repo).resolve()
        resolved_target_dir = target_dir or resolve_target_directory(
            config,
            target=target,
            machine=machine,
            skill=skill,
        )
        records.append(
            SkillInstallRecord(
                skill=skill,
                source=source,
                target=resolved_target_dir / skill.name,
            )
        )
    return records


@dataclass(frozen=True)
class InstallResult:
    target_dirs: tuple[Path, ...]
    submodules_created: list[str]
    submodules_skipped: list[str]
    installed: list[str]
    skipped: list[str]
    missing: list[str]

    @property
    def target_dir(self) -> Path:
        if len(self.target_dirs) != 1:
            raise ValueError("Install used multiple target directories; use target_dirs instead")
        return self.target_dirs[0]


def install_skills(
    config: Config,
    target: str | None = None,
    machine: str | None = None,
    force: bool = False,
) -> InstallResult:
    if machine is not None and machine not in config.machines:
        raise ValueError(f"Unknown machine '{machine}' in configuration")

    records = build_install_records(
        config,
        enabled_only=True,
        target=target,
        machine=machine,
    )
    target_dirs = tuple(sorted({record.target.parent for record in records}))
    if not target_dirs:
        target_dirs = (resolve_target_directory(config, target=target, machine=machine),)
    for target_dir in target_dirs:
        target_dir.mkdir(parents=True, exist_ok=True)

    submodule_result = ensure_submodules_present(config)
    installed: list[str] = []
    skipped: list[str] = []
    missing: list[str] = []

    for record in records:
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
        installed.append(f"{record.skill.name}: {record.target} -> {record.source}")

    return InstallResult(
        target_dirs=target_dirs,
        submodules_created=submodule_result.created,
        submodules_skipped=submodule_result.skipped,
        installed=installed,
        skipped=skipped,
        missing=missing,
    )


def render_install_summary(result: InstallResult, console: Console) -> None:
    targets = ", ".join(str(target_dir) for target_dir in result.target_dirs)
    summary = Table(title=f"Install summary: {targets}")
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
