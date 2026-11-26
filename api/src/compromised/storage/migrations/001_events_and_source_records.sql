-- Sources mirror the registry (health columns arrive with #3).
create table sources (
    id text primary key,
    name text not null,
    endpoint text not null
);

-- Events are what readers see. Grouping (#5) attaches several source records to one event.
create table events (
    id bigint generated always as identity primary key,
    title text not null,
    published_at timestamptz not null,
    first_seen_at timestamptz not null,
    last_updated_at timestamptz not null
);
create index events_newest_first on events (published_at desc, id desc);

-- One row per fetched item. Plain text only: no feed HTML is ever stored.
create table source_records (
    id bigint generated always as identity primary key,
    source_id text not null references sources (id),
    guid text,
    canonical_url text not null unique,
    original_url text not null,
    headline text not null,
    excerpt text not null default '',
    published_at timestamptz not null,
    fetched_at timestamptz not null,
    metadata jsonb not null default '{}'::jsonb,
    event_id bigint not null references events (id),
    unique (source_id, guid)
);
create index source_records_event on source_records (event_id);
