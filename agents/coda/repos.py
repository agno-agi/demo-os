"""Repos configuration loader."""

from os import getenv
from pathlib import Path

import yaml


def load_repos_config() -> list[dict]:
    """Load repository config from repos.yaml."""
    config_path = Path(getenv("REPOS_CONFIG", str(Path(__file__).parent / "repos.yaml")))
    if not config_path.exists():
        return []
    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)
        return data.get("repos", []) if data else []
    except Exception:
        return []
