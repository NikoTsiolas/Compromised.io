-- Later revisions of a stored source record (#4 meets #5). A source record stays exactly as it
-- was first fetched (004_grouping.sql's trigger); when a later fetch of the same item carries
-- changed structured fields (MSRC: Microsoft's severity or exploited flag in a new revision),
-- the changed fields are appended here. The effective metadata of a record is its own,
-- overlaid with its revisions in order (storage.EFFECTIVE_METADATA).
create table source_record_revisions (
    id bigint generated always as identity primary key,
    record_id bigint not null references source_records (id),
    fetched_at timestamptz not null,          -- when the fetch that carried the revision ran
    revised_at timestamptz,                   -- the source's own revision date, when it gives one
    metadata jsonb not null                   -- only the fields that changed
);
create index source_record_revisions_record on source_record_revisions (record_id, id);

-- Revisions are evidence too: appended, never edited or deleted.
create function source_record_revisions_are_append_only() returns trigger language plpgsql as $$
begin
    raise exception 'source record revisions are never altered or deleted';
end $$;
create trigger source_record_revisions_append_only before update or delete
    on source_record_revisions for each row
    execute function source_record_revisions_are_append_only();
