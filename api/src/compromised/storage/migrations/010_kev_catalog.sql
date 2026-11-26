-- The whole CISA Known Exploited Vulnerabilities catalog (#15), kept apart from feed events.
-- The KEV adapter turns only entries added in the last 30 days into events; the per-month
-- history behind the homepage chart needs every entry, so each full catalog the worker fetches
-- replaces these rows in one transaction (a 304 leaves them as they are). Monthly counts are a
-- grouping over these rows, so they always match the catalog the rows came from.
create table kev_catalog_entries (
    cve text primary key,
    vendor text not null default '',
    product text not null default '',
    name text not null,
    date_added date not null,
    known_ransomware_use boolean not null default false
);
create index kev_catalog_entries_date_added on kev_catalog_entries (date_added desc);

-- One row: which catalog the entries came from, and the size it declared for itself.
create table kev_catalog (
    id boolean primary key default true check (id),
    version text,
    declared_count integer,
    entries integer not null,
    fetched_at timestamptz not null
);
