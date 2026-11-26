"""Re-derive every event's category, organization and tabs from its stored source records.

    uv run python -m compromised.reclassify     (pnpm db:reclassify)

Run it after migration 002 on a database that already holds events, or after changing the
classifier rules or the alias dictionary.
"""

import psycopg

from compromised import config
from compromised.pipeline import scope

if __name__ == "__main__":
    with psycopg.connect(config.load().database_url, autocommit=True) as conn:
        print(f"reclassified {scope.refresh_all(conn)} event(s)")
