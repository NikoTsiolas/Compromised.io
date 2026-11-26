-- Search (#10): event-level search fields, derived by scope.refresh_event from the event's source
-- records (which stay immutable) and stored on the event.
alter table events
    add column cves text[] not null default '{}',           -- every CVE its records name, sorted
    add column threat_actors text[] not null default '{}',  -- groups named by text or claim source
    add column attack_vector text,                          -- pipeline.search_terms label, or null
    add column search_vector tsvector not null default ''::tsvector;

create index events_cves on events using gin (cves);
create index events_search_vector on events using gin (search_vector);
create index events_published on events (published_at desc, id desc)
    where cardinality(tabs) > 0;

-- Backfill what SQL alone can derive. Threat actors, attack vectors and the full search document
-- come from `pnpm db:reclassify` (scope.refresh_all) on a database that already holds events.
update events e set cves = coalesce(
    (select array_agg(distinct c order by c)
     from source_records r cross join unnest(r.cves) c where r.event_id = e.id),
    '{}');
update events e set search_vector =
    setweight(to_tsvector('english', e.title || ' ' || coalesce(e.organization, '')), 'A')
    || setweight(to_tsvector('english', coalesce(
        (select string_agg(r.excerpt, ' ') from source_records r where r.event_id = e.id), '')), 'C');
