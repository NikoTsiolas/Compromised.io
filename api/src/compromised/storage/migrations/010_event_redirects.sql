-- Event pages (#11) are addressed by event id. Regrouping (deduplicator.move_record) can delete
-- an event whose last record moved elsewhere; its old address then leads to the event that
-- record joined. One row per deleted event, always pointing at an event that exists: when the
-- target is itself deleted later, every row pointing at it is moved on to the new target in the
-- same transaction (the foreign key is checked at commit, so the move can follow the delete).
create table event_redirects (
    from_event_id bigint primary key,
    to_event_id bigint not null references events (id) deferrable initially deferred,
    created_at timestamptz not null default now()
);
create index event_redirects_to on event_redirects (to_event_id);
