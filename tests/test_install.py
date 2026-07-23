from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_skills.config import Config, Machine, Repository, Skill
from agent_skills.git_ops import ensure_submodules_present, uninstall_submodule
from agent_skills.install import install_skills


class InstallTests(unittest.TestCase):
    def test_ensure_submodules_present_adds_only_missing_repositories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            existing_path = root / "external" / "existing"
            existing_path.mkdir(parents=True)
            missing_path = root / "external" / "missing"

            config = Config(
                root=root,
                default_target=root / "target",
                repositories={
                    "existing": Repository("existing", existing_path, "https://example.com/existing.git"),
                    "missing": Repository("missing", missing_path, "https://example.com/missing.git"),
                },
                skills=[],
                update_exclude=set(),
            )

            calls: list[tuple[Path, str, Path]] = []

            def fake_submodule_add(repo_root: Path, url: str, repo_path: Path):
                calls.append((repo_root, url, repo_path))
                missing_path.mkdir(parents=True)

                class Result:
                    returncode = 0
                    stdout = ""
                    stderr = ""

                return Result()

            with patch("agent_skills.git_ops.run_git_submodule_add", side_effect=fake_submodule_add):
                result = ensure_submodules_present(config)

            self.assertEqual(
                calls,
                [(root, "https://example.com/missing.git", Path("external/missing"))],
            )
            self.assertEqual(len(result.created), 1)
            self.assertEqual(len(result.skipped), 1)

    def test_install_skills_links_after_creating_missing_submodules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "linked-skills"
            source = root / "external" / "obsidian" / "daily-notes"

            config = Config(
                root=root,
                default_target=target,
                repositories={
                    "obsidian": Repository(
                        "obsidian",
                        root / "external" / "obsidian",
                        "https://example.com/obsidian.git",
                    )
                },
                skills=[Skill(name="daily-notes", repo="external/obsidian/daily-notes", enabled=True)],
                update_exclude=set(),
            )

            def fake_ensure_submodules_present(_: Config):
                source.mkdir(parents=True)

                class Result:
                    created = ["obsidian -> https://example.com/obsidian.git (external/obsidian)"]
                    skipped = []

                return Result()

            with patch("agent_skills.install.ensure_submodules_present", side_effect=fake_ensure_submodules_present):
                result = install_skills(config)

            link_path = target / "daily-notes"
            self.assertTrue(link_path.is_symlink())
            self.assertEqual(link_path.resolve(), source.resolve())
            self.assertEqual(len(result.submodules_created), 1)
            self.assertEqual(result.missing, [])

    def test_install_skills_uses_machine_default_and_skill_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work_target = root / "work-skills"
            project_target = root / "project-skills"
            first_source = root / "skills" / "first"
            second_source = root / "skills" / "second"
            first_source.mkdir(parents=True)
            second_source.mkdir(parents=True)

            config = Config(
                root=root,
                default_target=root / "default-skills",
                repositories={},
                skills=[
                    Skill(name="first", repo="skills/first", enabled=True),
                    Skill(
                        name="second",
                        repo="skills/second",
                        enabled=True,
                        install_targets={"work": project_target},
                    ),
                ],
                update_exclude=set(),
                machines={
                    "work": Machine(
                        name="work",
                        default_target=work_target,
                        hostnames=(),
                    )
                },
            )

            with patch("agent_skills.install.ensure_submodules_present") as ensure:
                ensure.return_value.created = []
                ensure.return_value.skipped = []
                result = install_skills(config, machine="work")

            self.assertEqual((work_target / "first").resolve(), first_source.resolve())
            self.assertEqual((project_target / "second").resolve(), second_source.resolve())
            self.assertEqual(result.target_dirs, (project_target, work_target))

    def test_explicit_target_overrides_machine_routing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            explicit_target = root / "explicit-skills"
            source = root / "skills" / "daily-notes"
            source.mkdir(parents=True)

            config = Config(
                root=root,
                default_target=root / "default-skills",
                repositories={},
                skills=[
                    Skill(
                        name="daily-notes",
                        repo="skills/daily-notes",
                        enabled=True,
                        install_targets={"work": root / "project-skills"},
                    )
                ],
                update_exclude=set(),
                machines={
                    "work": Machine(
                        name="work",
                        default_target=root / "work-skills",
                        hostnames=(),
                    )
                },
            )

            with patch("agent_skills.install.ensure_submodules_present") as ensure:
                ensure.return_value.created = []
                ensure.return_value.skipped = []
                result = install_skills(
                    config,
                    target=str(explicit_target),
                    machine="work",
                )

            self.assertEqual((explicit_target / "daily-notes").resolve(), source.resolve())
            self.assertEqual(result.target_dir, explicit_target.resolve())

    def test_install_skills_rejects_unknown_machine(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = Config(
                root=root,
                default_target=root / "default-skills",
                repositories={},
                skills=[],
                update_exclude=set(),
            )

            with self.assertRaisesRegex(ValueError, "Unknown machine 'work'"):
                install_skills(config, machine="work")

    def test_uninstall_submodule_deinitializes_removes_and_cleans_modules_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_path = root / "external" / "obsidian"
            repo_path.mkdir(parents=True)
            modules_path = root / ".git" / "modules" / "external" / "obsidian"
            modules_path.mkdir(parents=True)

            config = Config(
                root=root,
                default_target=root / "target",
                repositories={
                    "obsidian": Repository("obsidian", repo_path, "https://example.com/obsidian.git"),
                },
                skills=[],
                update_exclude=set(),
            )

            calls: list[tuple[str, Path, Path]] = []

            def fake_submodule_deinit(repo_root: Path, relative_path: Path):
                calls.append(("deinit", repo_root, relative_path))

                class Result:
                    returncode = 0
                    stdout = ""
                    stderr = ""

                return Result()

            def fake_git_rm(repo_root: Path, relative_path: Path):
                calls.append(("rm", repo_root, relative_path))

                class Result:
                    returncode = 0
                    stdout = ""
                    stderr = ""

                return Result()

            with (
                patch("agent_skills.git_ops.run_git_submodule_deinit", side_effect=fake_submodule_deinit),
                patch("agent_skills.git_ops.run_git_rm", side_effect=fake_git_rm),
            ):
                removed_path = uninstall_submodule(config, "obsidian")

            self.assertEqual(removed_path, Path("external/obsidian"))
            self.assertEqual(
                calls,
                [
                    ("deinit", root, Path("external/obsidian")),
                    ("rm", root, Path("external/obsidian")),
                ],
            )
            self.assertFalse(modules_path.exists())


if __name__ == "__main__":
    unittest.main()
