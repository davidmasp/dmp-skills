from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from agent_skills.config import Config, Skill
from agent_skills.validate import validate_skills


class ValidateSkillsTests(unittest.TestCase):
    def test_validate_accepts_minimal_enabled_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skills" / "daily-notes"
            (skill_dir / "agents").mkdir(parents=True)
            (skill_dir / "references").mkdir()
            (skill_dir / "scripts").mkdir()
            (skill_dir / "SKILL.md").write_text(
                textwrap.dedent(
                    """
                    ---
                    name: daily-notes
                    description: Manage daily notes.
                    ---

                    # Daily Notes
                    """
                ).lstrip(),
                encoding="utf-8",
            )
            (skill_dir / "agents" / "openai.yaml").write_text(
                textwrap.dedent(
                    """
                    interface:
                      display_name: "Daily Notes"
                    """
                ).lstrip(),
                encoding="utf-8",
            )

            result = validate_skills(_config(root, [Skill("daily-notes", "skills/daily-notes", True)]))

            self.assertTrue(result.ok)
            self.assertEqual(result.checked, 1)

    def test_validate_reports_missing_skill_md_and_ignores_disabled_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "enabled").mkdir()

            result = validate_skills(
                _config(
                    root,
                    [
                        Skill("enabled", "enabled", True),
                        Skill("disabled", "missing-disabled", False),
                    ],
                )
            )

            self.assertEqual(result.checked, 1)
            self.assertEqual([issue.message for issue in result.issues], ["missing SKILL.md"])

    def test_validate_reports_frontmatter_name_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                textwrap.dedent(
                    """
                    ---
                    name: other
                    description: Wrong name.
                    ---
                    """
                ).lstrip(),
                encoding="utf-8",
            )

            result = validate_skills(_config(root, [Skill("expected", "skill", True)]))

            self.assertEqual(len(result.issues), 1)
            self.assertIn("does not match configured name", result.issues[0].message)

    def test_validate_reports_invalid_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("---\nname skill\n---\n", encoding="utf-8")

            result = validate_skills(_config(root, [Skill("skill", "skill", True)]))

            self.assertEqual(len(result.issues), 1)
            self.assertIn("frontmatter is invalid", result.issues[0].message)

    def test_validate_reports_clutter_and_unexpected_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: skill\ndescription: Test skill.\n---\n",
                encoding="utf-8",
            )
            (skill_dir / ".DS_Store").write_text("", encoding="utf-8")
            (skill_dir / "notes.txt").write_text("scratch", encoding="utf-8")

            result = validate_skills(_config(root, [Skill("skill", "skill", True)]))

            messages = sorted(issue.message for issue in result.issues)
            self.assertEqual(messages, ["unexpected top-level skill entry", "unnecessary clutter file or directory"])

    def test_validate_accepts_top_level_markdown_reference_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: skill\ndescription: Test skill.\n---\n",
                encoding="utf-8",
            )
            (skill_dir / "MISSION-FORMAT.md").write_text("# Mission Format\n", encoding="utf-8")
            (skill_dir / "LEARNING-RECORD-FORMAT.md").write_text("# Learning Record Format\n", encoding="utf-8")

            result = validate_skills(_config(root, [Skill("skill", "skill", True)]))

            self.assertTrue(result.ok)

    def test_validate_accepts_folded_frontmatter_and_singular_reference_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skill"
            (skill_dir / "reference").mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                textwrap.dedent(
                    """
                    ---
                    name: skill
                    description: >-
                      Drive a live notebook and inspect its state.
                    allowed-tools: Bash(script.sh *), Read
                    ---
                    """
                ).lstrip(),
                encoding="utf-8",
            )

            result = validate_skills(_config(root, [Skill("skill", "skill", True)]))

            self.assertTrue(result.ok)

    def test_validate_reports_unexpected_agents_file_and_invalid_openai_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skill"
            agents_dir = skill_dir / "agents"
            agents_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: skill\ndescription: Test skill.\n---\n",
                encoding="utf-8",
            )
            (agents_dir / "claude.yaml").write_text("name: skill\n", encoding="utf-8")
            (agents_dir / "openai.yaml").write_text("interface\n", encoding="utf-8")

            result = validate_skills(_config(root, [Skill("skill", "skill", True)]))

            messages = sorted(issue.message for issue in result.issues)
            self.assertEqual(
                messages,
                [
                    "invalid YAML: line 1 is not a mapping or list item",
                    "unexpected agents entry; only openai.yaml is supported",
                ],
            )

    def test_validate_reports_tab_indented_openai_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skill"
            agents_dir = skill_dir / "agents"
            agents_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: skill\ndescription: Test skill.\n---\n",
                encoding="utf-8",
            )
            (agents_dir / "openai.yaml").write_text("interface:\n\tdisplay_name: Skill\n", encoding="utf-8")

            result = validate_skills(_config(root, [Skill("skill", "skill", True)]))

            self.assertEqual([issue.message for issue in result.issues], ["invalid YAML: line 2 uses tab indentation"])


def _config(root: Path, skills: list[Skill]) -> Config:
    return Config(
        root=root,
        default_target=root / "target",
        repositories={},
        skills=skills,
        update_exclude=set(),
    )


if __name__ == "__main__":
    unittest.main()
