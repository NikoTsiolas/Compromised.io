"""Compromised: API and ingestion worker.

Module map (seams named in the MVP spec, issue #1). Modules marked "later" do not exist yet;
add them as their tickets land rather than growing existing modules past their job.

- ``sources``                  source registry: one declarative entry per source
- ``records``                  the shapes passed between stages (parsed item, source record, event)
- ``pipeline.fetcher``         HTTP fetching (hardened fetching and source health: #3)
- ``pipeline.parsers``         raw response bytes -> parsed items, one adapter per format
- ``pipeline.normalizer``      parsed item -> source record (canonical URL, plain-text excerpt, UTC)
- ``pipeline.deduplicator``    source record -> event (grouping: #5)
- ``pipeline.ingest``          runs the pipeline for one source response and stores the result
- ``storage``                  PostgreSQL access and SQL migrations
- ``api``                      read-only HTTP API (FastAPI)
- ``worker``                   ingestion worker process
- ``seed``                     loads captured samples for browser tests (never in production)
- later: entity extractor and classifier and scope rules (#6), verifier/scorer (#7),
  enricher (#8)
"""
