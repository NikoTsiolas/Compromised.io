-- The preview image an article page declares (pipeline.previews), kept apart from the source
-- record, which is evidence and never altered (see 004_grouping). One row per record, ever:
-- found (with its https address), none (no usable tag), failed, or skipped (not on a declared
-- article host, or disallowed by robots.txt). No row means not attempted yet.
create table article_previews (
    record_id bigint primary key references source_records (id),
    state text not null check (state in ('found', 'none', 'failed', 'skipped')),
    image_url text,
    attempted_at timestamptz not null
);
