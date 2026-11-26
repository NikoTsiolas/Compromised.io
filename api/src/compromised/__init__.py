"""Compromised: API and ingestion worker.

Module map (seams named in the MVP spec, issue #1). Modules marked "later" do not exist yet;
add them as their tickets land rather than growing existing modules past their job.

- ``sources``                  source registry: one declarative entry per source
- ``records``                  the shapes passed between stages (parsed item, source record, event)
- ``pipeline.fetcher``         allow-listed HTTPS fetching with size cap, timeouts, retries, 304s
- ``pipeline.parsers``         raw response bytes -> parsed items, one adapter per format
- ``pipeline.normalizer``      parsed item -> source record (canonical URL, plain-text excerpt, UTC)
- ``pipeline.extractor``       which organization or product a record is about (#6)
- ``pipeline.classifier``      rule-based category, commentary flag, exploited/critical (#6)
- ``pipeline.scope``           which feed tabs an event appears in (#6)
- ``pipeline.deduplicator``    source record -> event (grouping: #5)
- ``pipeline.ingest``          runs the pipeline for one source response and stores the result
- ``pipeline.enricher``        one LLM call per new event; schema-checked, rules as fallback
- ``pipeline.claude``          the real model client behind the enricher (Claude Haiku)
- ``pipeline.actions``         action lines a source states in a structured field (CISA KEV)
- ``storage``                  PostgreSQL access and SQL migrations
- ``health``                   per-source health and overall ingestion status
- ``api``                      read-only HTTP API (FastAPI)
- ``worker``                   ingestion worker process
- ``seed``                     loads captured samples for browser tests (never in production)
- later: verifier/scorer (#7)
"""
