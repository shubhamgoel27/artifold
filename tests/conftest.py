import pytest

from artifold import provenance


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    """Point the provenance store at a temp file so tests never touch the
    user's real cache."""
    monkeypatch.setattr(provenance, "STORE", tmp_path / "provenance.json")
