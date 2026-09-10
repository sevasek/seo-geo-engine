from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PROFILE_DIR = REPO_ROOT / "examples" / "sample-profile"


@pytest.fixture(scope="session")
def sample_profile_path() -> Path:
    return SAMPLE_PROFILE_DIR / "site.yaml"


@pytest.fixture(scope="session")
def sample_crawl_path() -> Path:
    return SAMPLE_PROFILE_DIR / "fixtures" / "site-crawl-sample.json"
