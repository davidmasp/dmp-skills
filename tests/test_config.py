from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from agent_skills.config import load_config


class LoadConfigTests(unittest.TestCase):
    def test_load_config_reads_repository_urls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "skills.toml"
            config_path.write_text(
                textwrap.dedent(
                    """
                    [installation]
                    default_target = "./target"

                    [repositories.obsidian]
                    path = "external/obsidian-skills"
                    url = "https://example.com/obsidian.git"

                    [[skills.skill]]
                    name = "daily-notes"
                    repo = "obsidian"
                    enabled = true
                    """
                ).strip()
            )

            config = load_config(config_path)

            self.assertEqual(
                config.repositories["obsidian"].url,
                "https://example.com/obsidian.git",
            )
            self.assertEqual(config.default_target, (root / "target").resolve())
            self.assertEqual(config.machines, {})
            self.assertEqual(config.skills[0].install_targets, {})

    def test_load_config_reads_machine_and_skill_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "skills.toml"
            config_path.write_text(
                textwrap.dedent(
                    """
                    [installation]
                    default_target = "./default-target"

                    [machines.work]
                    default_target = "./work-target"
                    hostnames = ["workstation.local"]

                    [repositories.obsidian]
                    path = "external/obsidian-skills"
                    url = "https://example.com/obsidian.git"

                    [[skills.skill]]
                    name = "daily-notes"
                    repo = "external/obsidian-skills/daily-notes"
                    enabled = true
                    install_targets = { work = "./project-skills" }
                    """
                ).strip()
            )

            config = load_config(config_path)

            self.assertEqual(config.machines["work"].default_target, (root / "work-target").resolve())
            self.assertEqual(config.machines["work"].hostnames, ("workstation.local",))
            self.assertEqual(
                config.skills[0].install_targets["work"],
                (root / "project-skills").resolve(),
            )

    def test_load_config_rejects_skill_target_for_unknown_machine(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "skills.toml"
            config_path.write_text(
                textwrap.dedent(
                    """
                    [repositories.obsidian]
                    path = "external/obsidian-skills"
                    url = "https://example.com/obsidian.git"

                    [[skills.skill]]
                    name = "daily-notes"
                    repo = "external/obsidian-skills/daily-notes"
                    enabled = true
                    install_targets = { work = "./project-skills" }
                    """
                ).strip()
            )

            with self.assertRaisesRegex(ValueError, "unknown machine 'work'"):
                load_config(config_path)

    def test_load_config_requires_repository_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "skills.toml"
            config_path.write_text(
                textwrap.dedent(
                    """
                    [repositories.obsidian]
                    path = "external/obsidian-skills"
                    """
                ).strip()
            )

            with self.assertRaisesRegex(ValueError, "missing a url"):
                load_config(config_path)

    def test_load_config_rejects_duplicate_skill_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "skills.toml"
            config_path.write_text(
                textwrap.dedent(
                    """
                    [repositories.obsidian]
                    path = "external/obsidian-skills"
                    url = "https://example.com/obsidian.git"

                    [[skills.skill]]
                    name = "defuddle"
                    repo = "external/obsidian-skills/skills/defuddle"
                    enabled = true

                    [[skills.skill]]
                    name = "defuddle"
                    repo = "external/obsidian-skills/skills/other"
                    enabled = true
                    """
                ).strip()
            )

            with self.assertRaisesRegex(ValueError, "Duplicate skill name"):
                load_config(config_path)


if __name__ == "__main__":
    unittest.main()
