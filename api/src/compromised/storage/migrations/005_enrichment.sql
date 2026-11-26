-- LLM enrichment (#8). The enricher's own output is kept apart from the rule classifier's, so
-- re-running the rules (scope.refresh_event) re-applies it instead of losing it.
-- The model never writes verification status or score (#7).
alter table events
    add column enrichment_state text not null default 'awaiting'
        check (enrichment_state in ('awaiting', 'enriched')),
    add column enrichment_attempts integer not null default 0,  -- rejected model replies
    add column enriched_at timestamptz,
    add column summary text,              -- plain-language summary, AI-written, plain text
    add column ai_category text,          -- the model's category, when it gave a valid one
    add column ai_commentary boolean,
    add column ai_organization text,      -- only when the rules found none and the input names it
    add column ai_action_line text,       -- only when the input states the action
    add column action_line text;          -- what readers see; derived in scope.refresh_event

create index events_awaiting_enrichment on events (published_at desc, id desc)
    where enrichment_state = 'awaiting';

-- Model calls made per UTC day, for the daily cap.
create table enrichment_usage (
    day date primary key,
    calls integer not null default 0
);
