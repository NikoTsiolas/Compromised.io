-- Registry mirror (the code registry in compromised/sources.py is the source of truth) and
-- per-source fetch health. Validators are those of the last response that was parsed and stored.
alter table sources
    add column tier text,
    add column weight integer,
    add column interval_seconds integer,
    add column etag text,
    add column last_modified text,
    add column last_attempt_at timestamptz,
    add column last_success_at timestamptz,
    add column last_error text,
    add column last_error_at timestamptz,
    add column consecutive_failures integer not null default 0;
