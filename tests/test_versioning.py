"""Versioning-policy canary: CHANGELOG and package version must agree.

Does not score checks or touch fixtures. The sample profile remains the
runtime compatibility canary via the rest of this suite
(`examples/sample-profile/`, see `tests/conftest.py`).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_changelog_exists_mentions_0_1_0_and_matches_pyproject():
    changelog_path = REPO_ROOT / "CHANGELOG.md"
    assert changelog_path.is_file(), "CHANGELOG.md must exist at the repo root"
    changelog = changelog_path.read_text(encoding="utf-8")
    assert "0.1.0" in changelog

    pyproject = tomllib.loads(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    version = pyproject["project"]["version"]
    assert version == "0.1.0"
    assert version in changelog


def test_versioning_policy_names_semver_for_pinned_profiles():
    policy = (REPO_ROOT / "docs" / "design" / "versioning.md").read_text(
        encoding="utf-8"
    )
    for token in ("MAJOR", "MINOR", "PATCH", "profile"):
        assert token in policy, f"versioning policy must mention {token!r}"
    assert ">=0.1,<0.2" in policy
