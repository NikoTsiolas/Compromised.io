from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def real_sample(name: str) -> bytes:
    """Bytes of a real captured feed response (see fixtures/real/README.md)."""
    return (FIXTURES / "real" / name).read_bytes()
