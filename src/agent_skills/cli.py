from __future__ import annotations

import typer
from rich.console import Console

from .config import load_config
from .git_ops import uninstall_submodule, update_all_repositories, update_repository
from .install import install_skills, render_install_summary
from .validate import validate_skills

app = typer.Typer(help="Manage AI agent skills from a Git-backed repository.")
console = Console()


@app.command()
def install(
    target: str | None = typer.Option(None, help="Override installation target directory."),
    force: bool = typer.Option(False, "--force", help="Replace existing targets that are not the expected symlink."),
    config: str = typer.Option("skills.toml", help="Path to the TOML configuration file."),
) -> None:
    cfg = load_config(config)
    try:
        result = install_skills(cfg, target=target, force=force)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    render_install_summary(result, console)
    if result.missing:
        raise typer.Exit(code=1)


@app.command("update-submodules")
def update_submodules(
    include_excluded: bool = typer.Option(
        False,
        "--include-excluded",
        help="Update repositories even if they contain skills listed in [update].exclude.",
    ),
    config: str = typer.Option("skills.toml", help="Path to the TOML configuration file."),
) -> None:
    cfg = load_config(config)
    selection, result = update_all_repositories(cfg, include_excluded=include_excluded)

    if not selection.repo_paths:
        console.print("No repositories selected for update.")
        raise typer.Exit(code=0)

    if selection.skipped_repositories:
        console.print(f"Skipped repositories due to exclusions: {', '.join(selection.skipped_repositories)}")
    if result is not None and result.stdout:
        console.print(result.stdout.strip())
    if result is not None and result.stderr:
        console.print(result.stderr.strip())
    if result is not None and result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@app.command("update-skill")
def update_skill(
    repo: str = typer.Argument(..., help="Repository key from [repositories]."),
    config: str = typer.Option("skills.toml", help="Path to the TOML configuration file."),
) -> None:
    cfg = load_config(config)
    result = update_repository(cfg, repo)
    if result.stdout:
        console.print(result.stdout.strip())
    if result.stderr:
        console.print(result.stderr.strip())
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@app.command("uninstall-submodule")
def uninstall_submodule_command(
    repo: str = typer.Argument(..., help="Repository key from [repositories]."),
    config: str = typer.Option("skills.toml", help="Path to the TOML configuration file."),
) -> None:
    cfg = load_config(config)
    try:
        repo_path = uninstall_submodule(cfg, repo)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print(f"Removed submodule {repo} ({repo_path})")


@app.command()
def validate(
    config: str = typer.Option("skills.toml", help="Path to the TOML configuration file."),
) -> None:
    cfg = load_config(config)
    result = validate_skills(cfg)

    if result.ok:
        console.print(f"Validated {result.checked} enabled skills.")
        return

    for issue in result.issues:
        try:
            path = issue.path.relative_to(cfg.root)
        except ValueError:
            path = issue.path
        console.print(f"{issue.skill}: {path}: {issue.message}")
    raise typer.Exit(code=1)
