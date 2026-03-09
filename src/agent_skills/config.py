from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import tomllib


@dataclass(frozen=True)
class Repository:
    name: str
    path: Path
    url: str


@dataclass(frozen=True)
class Skill:
    name: str
    repo: str
    enabled: bool

    @property
    def qualified_name(self) -> str:
        return f"{self.repo} -> {self.name}"


@dataclass(frozen=True)
class Config:
    root: Path
    default_target: Path
    repositories: dict[str, Repository]
    skills: list[Skill]
    update_exclude: set[str]

    def repository(self, name: str) -> Repository:
        try:
            return self.repositories[name]
        except KeyError as exc:
            raise ValueError(f"Unknown repository '{name}' in configuration") from exc


def _expand_path(value: str, root: Path) -> Path:
    expanded = Path(os.path.expanduser(value))
    if expanded.is_absolute():
        return expanded
    return (root / expanded).resolve()


def load_config(config_path: str | Path = "skills.toml") -> Config:
    config_file = Path(config_path).resolve()
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    root = config_file.parent
    with config_file.open("rb") as fh:
        data = tomllib.load(fh)

    installation = data.get("installation", {})
    default_target_raw = installation.get("default_target", "~/.agents/skills")
    default_target = _expand_path(default_target_raw, root)

    repositories_raw = data.get("repositories")
    if not isinstance(repositories_raw, dict) or not repositories_raw:
        raise ValueError("Configuration must define at least one repository under [repositories]")

    repositories: dict[str, Repository] = {}
    for repo_name, repo_data in repositories_raw.items():
        repo_path = repo_data.get("path")
        repo_url = repo_data.get("url")
        if not repo_path:
            raise ValueError(f"Repository '{repo_name}' is missing a path")
        if not repo_url:
            raise ValueError(f"Repository '{repo_name}' is missing a url")
        repositories[repo_name] = Repository(name=repo_name, path=_expand_path(repo_path, root), url=str(repo_url))

    skills_block = data.get("skills", {})
    skills_raw = skills_block.get("skill", [])
    if not isinstance(skills_raw, list):
        raise ValueError("Configuration key [[skills.skill]] must be a list of tables")

    skills: list[Skill] = []
    seen_names: set[str] = set()
    seen_sources: set[str] = set()
    for item in skills_raw:
        name = item.get("name")
        repo = item.get("repo")
        enabled = bool(item.get("enabled", False))
        if not name or not repo:
            raise ValueError("Each skill must define 'name' and 'repo'")
        if name in seen_names:
            raise ValueError(f"Duplicate skill name found for target '{name}'")
        if repo in seen_sources:
            raise ValueError(f"Duplicate skill source path found for '{repo}'")
        seen_names.add(str(name))
        seen_sources.add(str(repo))
        skills.append(Skill(name=str(name), repo=str(repo), enabled=enabled))

    update_block = data.get("update", {})
    exclude_raw = update_block.get("exclude", [])
    if not isinstance(exclude_raw, list):
        raise ValueError("[update].exclude must be a list")
    update_exclude = {str(entry) for entry in exclude_raw}

    return Config(
        root=root,
        default_target=default_target,
        repositories=repositories,
        skills=skills,
        update_exclude=update_exclude,
    )
