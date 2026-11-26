# LLM usage

- 2026-11-26: The brief left AI classification optional and Claude recommended rules only. Niko decided an LLM belongs in the MVP, mainly for a brief plain-language synopsis.
- 2026-11-26: One Claude Haiku call per event returns a structured result: category, affected organization, whether it is a real incident or commentary, and a one-to-two sentence plain-language summary shown with an "AI summary" label.
- 2026-11-26: Limits agreed:
  - The model sees only the headline and excerpt, marked as untrusted text. Its output is stored as plain text.
  - It never sets verification status or the confidence score.
  - Deterministic rules remain as the fallback when the API is unavailable.
  - An action line ("Update Windows now") appears only when a source states that action; CISA's required-action field is used for exploited flaws. Otherwise nothing is shown.
  - A daily cap (default 500 events, configurable) stops calls and falls back to rules.
- 2026-11-26: Niko creates the Anthropic API key and places it in the server environment himself.

Related: [Trust labels and score](trust-labels-and-score.md).

## Enrichment as built, 2026-11-26
Ticket #8, built by an Opus subagent on branch `claude/serene-goodall-c05998` (commit named in the merge):
- The model was Claude Haiku 5.5 (`claude-haiku-5-5`), called through the `anthropic` Python SDK with structured JSON output and effort `low`. It received one JSON object, headline and excerpt only, inside `<untrusted_feed_item>` tags with every `<` and `>` escaped, and a system prompt saying the wrapped text is data, not instructions.
- The reply had exactly six fields: category, affected organization, commentary flag, summary (at most 320 characters), action line (at most 160) and `action_quote`, the input's own words stating the action. Any other field, a wrong type, an unknown category or an over-long text rejected the whole reply. Markup was stripped; a summary carrying a link was rejected.
- Checks beyond the schema: an organization was kept only if the rules found none, the input named it and it was not a threat actor or reporter; an action line was kept only if its quote appeared in the input and it named no domain or email address; attacker-claim-only events never got an action line from the model.
- The model could change category and commentary flag; it never wrote verification status or score. Its output was stored in its own columns (`ai_*`, `summary`), so re-running the rules kept it.
- Action lines by rule: a record's metadata key `required_action` (the KEV adapter, #4, must fill it from `requiredAction`) gave the first sentence of that field, cut at a clause when longer than 160 characters. The real KEV entries on this date became "Apply mitigations in accordance with vendor instructions." It took precedence over the model's line.
- Failure handling: an outage, timeout or rate limit left the event on rules (`enrichment: "rules"`) and ended that pass's enrichment; the next worker pass retried waiting events, newest first. A refusal or rejected reply counted as an attempt; after 3 the event stayed on rules. Every call, failed or not, counted against `ENRICHMENT_DAILY_CAP` (default 500, per UTC day).
- With no `ANTHROPIC_API_KEY` the worker logged "enrichment off" and ran on rules. No real API call was made while building it; tests used a fake client and a mock HTTP transport.
- `GET /v1/events` gained `summary`, `action_line` and `enrichment` ("ai" or "rules"). The bare page showed "AI summary: ..." and "Action: ..." as plain text, for #9 to restyle.
