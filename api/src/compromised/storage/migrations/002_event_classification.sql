-- Category, commentary flag, affected organization and feed scope (#6).
-- Events stored before this migration get defaults that put them in no tab; run
-- `python -m compromised.pipeline.scope` (pnpm db:reclassify) to classify them.
alter table events
    add column category text not null default 'other',
    add column commentary boolean not null default false,
    add column organization text,          -- null means unknown
    add column organization_key text,      -- catalog key when the organization is in it
    add column logo_key text,
    add column people_use boolean not null default false,
    add column exploited boolean not null default false,
    add column critical boolean not null default false,
    add column claim_only boolean not null default false,
    add column tabs text[] not null default '{}';

create index events_tabs on events using gin (tabs);
create index events_category on events (category);
create index events_organization_key on events (organization_key);
