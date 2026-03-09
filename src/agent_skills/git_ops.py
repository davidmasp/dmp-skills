from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import shutil

from .config import Config


@dataclass(frozen=True)
class SubmoduleEnsureResult:
    created: list[str]
    skipped: list[str]


def run_git_submodule_update(repo_root: Path, repo_paths: list[Path] | None = None) -> subprocess.CompletedProcess[str]:
    command = ["git", "submodule", "update", "--remote", "--merge"]
    if repo_paths:
        command.extend(str(path) for path in repo_paths)
    return subprocess.run(command, cwd=repo_root, check=False, text=True, capture_output=True)


def run_git_submodule_add(repo_root: Path, url: str, repo_path: Path) -> subprocess.CompletedProcess[str]:
    command = ["git", "submodule", "add", url, str(repo_path)]
    return subprocess.run(command, cwd=repo_root, check=False, text=True, capture_output=True)


def run_git_submodule_deinit(repo_root: Path, repo_path: Path) -> subprocess.CompletedProcess[str]:
    command = ["git", "submodule", "deinit", "-f", "--", str(repo_path)]
    return subprocess.run(command, cwd=repo_root, check=False, text=True, capture_output=True)


def run_git_rm(repo_root: Path, repo_path: Path) -> subprocess.CompletedProcess[str]:
    command = ["git", "rm", "-f", str(repo_path)]
    return subprocess.run(command, cwd=repo_root, check=False, text=True, capture_output=True)


def ensure_submodules_present(config: Config) -> SubmoduleEnsureResult:
    created: list[str] = []
    skipped: list[str] = []

    for repository in config.repositories.values():
        if repository.path.exists():
            skipped.append(f"{repository.name} already exists at {repository.path}")
            continue

        try:
            repo_path = repository.path.relative_to(config.root)
        except ValueError as exc:
            raise ValueError(
                f"Repository '{repository.name}' path must be inside the config root: {repository.path}"
            ) from exc

        repository.path.parent.mkdir(parents=True, exist_ok=True)
        result = run_git_submodule_add(config.root, repository.url, repo_path)
        if result.returncode != 0:
            stderr = result.stderr.strip() or result.stdout.strip() or "git submodule add failed"
            raise ValueError(f"Failed to add submodule '{repository.name}': {stderr}")
        created.append(f"{repository.name} -> {repository.url} ({repo_path})")

    return SubmoduleEnsureResult(created=created, skipped=skipped)


@dataclass(frozen=True)
class UpdateSelection:
    repo_paths: list[Path]
    skipped_repositories: list[str]


def select_repositories_for_update(config: Config, include_excluded: bool = False) -> UpdateSelection:
    excluded_repos = {
        qualified_name.split("/", 1)[0]
        for qualified_name in config.update_exclude
        if "/" in qualified_name
    }

    repo_paths: list[Path] = []
    skipped: list[str] = []
    for repo_name, repository in config.repositories.items():
        if excluded_repos and repo_name in excluded_repos and not include_excluded:
            skipped.append(repo_name)
            continue
        repo_paths.append(repository.path.relative_to(config.root))

    return UpdateSelection(repo_paths=repo_paths, skipped_repositories=skipped)


def update_all_repositories(
    config: Config, include_excluded: bool = False
) -> tuple[UpdateSelection, subprocess.CompletedProcess[str] | None]:
    selection = select_repositories_for_update(config, include_excluded=include_excluded)
    if not selection.repo_paths:
        return selection, None
    result = run_git_submodule_update(config.root, repo_paths=selection.repo_paths)
    return selection, result


def update_repository(config: Config, repo_name: str) -> subprocess.CompletedProcess[str]:
    repository = config.repository(repo_name)
    return run_git_submodule_update(config.root, [repository.path.relative_to(config.root)])


def uninstall_submodule(config: Config, repo_name: str) -> Path:
    repository = config.repository(repo_name)
    try:
        repo_path = repository.path.relative_to(config.root)
    except ValueError as exc:
        raise ValueError(
            f"Repository '{repository.name}' path must be inside the config root: {repository.path}"
        ) from exc

    deinit_result = run_git_submodule_deinit(config.root, repo_path)
    if deinit_result.returncode != 0:
        stderr = deinit_result.stderr.strip() or deinit_result.stdout.strip() or "git submodule deinit failed"
        raise ValueError(f"Failed to deinitialize submodule '{repository.name}': {stderr}")

    rm_result = run_git_rm(config.root, repo_path)
    if rm_result.returncode != 0:
        stderr = rm_result.stderr.strip() or rm_result.stdout.strip() or "git rm failed"
        raise ValueError(f"Failed to remove submodule '{repository.name}': {stderr}")

    modules_path = config.root / ".git" / "modules" / repo_path
    if modules_path.exists():
        shutil.rmtree(modules_path)

    return repo_path
