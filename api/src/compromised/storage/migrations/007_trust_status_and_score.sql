-- Verification status, reader-facing label and 0-100 confidence score (#7), derived by
-- pipeline.verifier from an event's source records and the registry's tiers and weights, and
-- stored by scope.refresh_event whenever an event gains or loses a record. The model never
-- writes these (see 005_enrichment.sql). Null until the event is first assessed; events stored
-- before this migration are assessed by `pnpm db:reclassify`.
alter table events
    add column status text
        check (status in ('confirmed', 'reported', 'claimed', 'investigating', 'disputed')),
    add column status_label text,
    add column score smallint check (score between 0 and 100),
    add column score_sources text[] not null default '{}',  -- publishers the score counted
    -- status, label and score are set together or not at all: a score never stands alone
    add constraint events_trust_together check (
        (status is null) = (score is null) and (status is null) = (status_label is null));

create index events_status on events (status);

-- Registry mirror: who an official source speaks for (sources.Source.government/organization).
alter table sources
    add column government boolean not null default false,
    add column organization text;
