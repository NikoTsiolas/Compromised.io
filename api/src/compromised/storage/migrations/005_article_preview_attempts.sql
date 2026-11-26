-- Whether the article page was asked for its preview image (pipeline.previews). One attempt per
-- record, ever: found, none (no usable tag), failed, or skipped (not on a declared article host,
-- or disallowed by robots.txt). NULL means not attempted yet.
alter table source_records
    add column preview_state text,
    add column preview_attempted_at timestamptz;
