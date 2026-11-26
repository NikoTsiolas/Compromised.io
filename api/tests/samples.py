from pathlib import Path

from compromised import sources
from compromised.sources import Source

FIXTURES = Path(__file__).parent / "fixtures"


def real_sample(name: str) -> bytes:
    """Bytes of a real captured feed response (see fixtures/real/README.md)."""
    return (FIXTURES / "real" / name).read_bytes()


def synthetic_sample(name: str) -> bytes:
    """Bytes of a hand-written input (see fixtures/synthetic/README.md). Not a real incident."""
    return (FIXTURES / "synthetic" / name).read_bytes()


def sample_source(source_id: str) -> Source:
    """The registry entry for a sampled source. Sample file names equal source ids."""
    return sources.by_id(source_id)
