-- Grouping duplicate coverage into events (#5).
-- Trigram similarity compares headlines of records about the same organization.
create extension if not exists pg_trgm;

-- The same article reached through two sources is one story: a canonical URL is now unique per
-- source, and a second source's record with that URL joins the first one's event.
alter table source_records drop constraint source_records_canonical_url_key;
alter table source_records add constraint source_records_source_canonical_url_key
    unique (source_id, canonical_url);
create index source_records_canonical_url on source_records (canonical_url);

-- CVE identifiers named anywhere in the item (headline or full summary), found at ingest.
alter table source_records add column cves text[] not null default '{}';
create index source_records_cves on source_records using gin (cves);
-- Records stored before this migration: best effort from headline and excerpt (the full summary
-- was not kept). Their events are not regrouped.
update source_records set cves = coalesce(
    (select array_agg(distinct upper(m[1]) order by upper(m[1]))
     from regexp_matches(headline || ' ' || excerpt, '\m(CVE-\d{4}-\d{4,7})\M', 'gi') m),
    '{}');
create index source_records_published_at on source_records (published_at);

-- Source records are evidence: once stored they are never edited or deleted. Only their
-- assignment to an event (event_id) may change, so a record can be moved to another event.
create function source_records_are_immutable() returns trigger language plpgsql as $$
begin
    if tg_op = 'DELETE' then
        raise exception 'source records are never deleted';
    end if;
    if (to_jsonb(new) - 'event_id') is distinct from (to_jsonb(old) - 'event_id') then
        raise exception 'source records are never altered; only event_id may change';
    end if;
    return new;
end $$;
create trigger source_records_immutable before update or delete on source_records
    for each row execute function source_records_are_immutable();
