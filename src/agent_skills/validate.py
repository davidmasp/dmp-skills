from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import Config, Skill


ALLOWED_TOP_LEVEL_ENTRIES = {"SKILL.md", "agents", "references", "scripts"}
ALLOWED_AGENTS_FILES = {"openai.yaml"}
CLUTTER_NAMES = {".DS_Store", "Thumbs.db", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
CLUTTER_SUFFIXES = {".pyc", ".pyo", ".swp", ".tmp"}


@dataclass(frozen=True)
class SkillValidationIssue:
    skill: str
    path: Path
    message: str


@dataclass(frozen=True)
class SkillValidationResult:
    checked: int
    issues: list[SkillValidationIssue]

    @property
    def ok(self) -> bool:
        return not self.issues


def validate_skills(config: Config) -> SkillValidationResult:
    issues: list[SkillValidationIssue] = []
    enabled_skills = [skill for skill in config.skills if skill.enabled]

    for skill in enabled_skills:
        skill_path = (config.root / skill.repo).resolve()
        issues.extend(_validate_skill(skill, skill_path))

    return SkillValidationResult(checked=len(enabled_skills), issues=issues)


def _validate_skill(skill: Skill, skill_path: Path) -> list[SkillValidationIssue]:
    issues: list[SkillValidationIssue] = []

    def add(path: Path, message: str) -> None:
        issues.append(SkillValidationIssue(skill=skill.name, path=path, message=message))

    if not skill_path.exists():
        add(skill_path, "skill directory does not exist")
        return issues
    if not skill_path.is_dir():
        add(skill_path, "skill path is not a directory")
        return issues

    skill_md = skill_path / "SKILL.md"
    if not skill_md.is_file():
        add(skill_md, "missing SKILL.md")
    else:
        frontmatter, frontmatter_error = _read_frontmatter(skill_md)
        if frontmatter_error is not None:
            add(skill_md, frontmatter_error)
        elif frontmatter is not None:
            frontmatter_name = frontmatter.get("name")
            description = frontmatter.get("description")
            if not frontmatter_name:
                add(skill_md, "frontmatter is missing non-empty name")
            elif frontmatter_name != skill.name:
                add(skill_md, f"frontmatter name '{frontmatter_name}' does not match configured name '{skill.name}'")
            if not description:
                add(skill_md, "frontmatter is missing non-empty description")

    issues.extend(_validate_layout(skill, skill_path))
    return issues


def _read_frontmatter(path: Path) -> tuple[dict[str, str] | None, str | None]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "SKILL.md must start with YAML frontmatter"

    end_index: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break

    if end_index is None:
        return None, "frontmatter is missing closing ---"

    frontmatter_lines = lines[1:end_index]
    data, error = _parse_flat_yaml_mapping(frontmatter_lines)
    if error is not None:
        return None, f"frontmatter is invalid: {error}"
    return data, None


def _parse_flat_yaml_mapping(lines: list[str]) -> tuple[dict[str, str], str | None]:
    data: dict[str, str] = {}
    for line_number, raw_line in enumerate(lines, start=2):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if raw_line[:1].isspace():
            return {}, f"line {line_number} uses nested content; expected key/value frontmatter"
        if ":" not in line:
            return {}, f"line {line_number} is missing ':'"
        key, value = line.split(":", 1)
        key = key.strip()
        if not key:
            return {}, f"line {line_number} has an empty key"
        data[key] = _unquote_scalar(value.strip())
    return data, None


def _unquote_scalar(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _validate_layout(skill: Skill, skill_path: Path) -> list[SkillValidationIssue]:
    issues: list[SkillValidationIssue] = []

    def add(path: Path, message: str) -> None:
        issues.append(SkillValidationIssue(skill=skill.name, path=path, message=message))

    for child in sorted(skill_path.iterdir()):
        if _is_clutter(child):
            add(child, "unnecessary clutter file or directory")
            continue
        if child.name not in ALLOWED_TOP_LEVEL_ENTRIES:
            add(child, "unexpected top-level skill entry")

    agents_dir = skill_path / "agents"
    if agents_dir.exists():
        if not agents_dir.is_dir():
            add(agents_dir, "agents must be a directory")
        else:
            for child in sorted(agents_dir.iterdir()):
                if _is_clutter(child):
                    add(child, "unnecessary clutter file or directory")
                elif child.name not in ALLOWED_AGENTS_FILES:
                    add(child, "unexpected agents entry; only openai.yaml is supported")
            openai_yaml = agents_dir / "openai.yaml"
            if openai_yaml.exists():
                if not openai_yaml.is_file():
                    add(openai_yaml, "agents/openai.yaml must be a file")
                else:
                    yaml_error = _validate_simple_yaml(openai_yaml)
                    if yaml_error is not None:
                        add(openai_yaml, f"invalid YAML: {yaml_error}")

    for directory_name in ("references", "scripts"):
        directory = skill_path / directory_name
        if directory.exists() and not directory.is_dir():
            add(directory, f"{directory_name} must be a directory")

    for descendant in skill_path.rglob("*"):
        if descendant.parent == skill_path or descendant.parent == agents_dir:
            continue
        if _is_clutter(descendant):
            add(descendant, "unnecessary clutter file or directory")

    return issues


def _is_clutter(path: Path) -> bool:
    return path.name in CLUTTER_NAMES or path.suffix in CLUTTER_SUFFIXES


def _validate_simple_yaml(path: Path) -> str | None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not any(line.strip() and not line.lstrip().startswith("#") for line in lines):
        return "file is empty"

    for line_number, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        leading_whitespace = raw_line[: len(raw_line) - len(raw_line.lstrip())]
        if "\t" in leading_whitespace:
            return f"line {line_number} uses tab indentation"
        indent = len(leading_whitespace)
        if indent % 2 != 0:
            return f"line {line_number} uses odd indentation"
        if ":" not in stripped and not stripped.startswith("- "):
            return f"line {line_number} is not a mapping or list item"
    return None
