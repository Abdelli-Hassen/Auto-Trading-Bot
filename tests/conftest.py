import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("ALLOW_SYNTHETIC_FALLBACK", "true")

from data.storage import DataStorage  # noqa: E402
from data.fetcher import DataFetcher  # noqa: E402


class OfflineFetcher(DataFetcher):
    """Always uses the simulated feed so tests never touch the network."""

    def __init__(self):
        super().__init__()
        self.data_source = "synthetic"

    def _use_synthetic(self):
        return True


@pytest.fixture(autouse=True)
def restore_config():
    """Tests change runtime settings; put every config value back afterwards."""
    import config
    snapshot = {k: v for k, v in vars(config).items() if k.isupper()}
    yield
    for k, v in snapshot.items():
        setattr(config, k, v)


@pytest.fixture
def storage(tmp_path):
    return DataStorage(tmp_path / "test.db")


@pytest.fixture
def fetcher():
    return OfflineFetcher()
