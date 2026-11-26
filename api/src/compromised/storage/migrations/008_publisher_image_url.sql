-- The image a publisher attached to an item in its own feed: one https URL per source record.
-- Only the URL is stored. The image itself is never downloaded, proxied or cached by us.
alter table source_records add column image_url text;
