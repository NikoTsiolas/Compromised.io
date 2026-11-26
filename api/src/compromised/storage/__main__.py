"""Apply pending migrations: ``uv run python -m compromised.storage migrate``."""

import argparse

from compromised import config, storage

parser = argparse.ArgumentParser(prog="compromised.storage")
parser.add_argument("command", choices=["migrate"])
parser.parse_args()

applied = storage.migrate(config.load().database_url)
print(f"applied {len(applied)} migration(s): {', '.join(applied) or 'none pending'}")
