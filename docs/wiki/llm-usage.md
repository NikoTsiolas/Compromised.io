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
