# Working agreements

- 2026-11-26: Niko asked for Fable to plan and Opus subagents to execute features. Claude (Fable) acts as chief of staff: writes the spec and tickets, delegates each ticket to an Opus subagent, reviews results and keeps this wiki.
- 2026-11-26: Process: spec and tickets are published as GitHub issues on `NikoTsiolas/Compromised.io` with the `ready-for-agent` label; tickets are implemented test-first on one integration branch, each in its own worktree.
- 2026-11-26: Niko dictates his answers by voice; transcripts can be garbled. Confirm anything ambiguous instead of guessing.
- 2026-11-26: When Niko says "your call", he wants a researched recommendation with reasons, then a decision, not a menu.
- 2026-11-26: Niko's own jobs: buy the domain in Cloudflare; create the Anthropic API key; later a Resend account; supply missing logos.
- 2026-11-26: Research notes and captured feed samples for subagents live outside the repo in `~/.claude/projects/-Users-nikotsiolas-Desktop-Projects-Compromised-io/research/`.

## Open questions on 2026-11-26
- What the "Impeccable" library is.
- Whether monospace for timestamps and identifiers matches what Niko said.
- Whether the MSRC feed carries severity. (Answered 2026-11-26: it does not; see Feed scope and sources.)
- Whether Niko holds a Bencho Pro licence.
- Which Postgres version Railway provisions.

## Later on 2026-11-26
- Niko said the project is public and open source. On this date the GitHub repository's visibility was still private and it had no licence file; which licence, and when to switch visibility, were not yet decided.
- Niko confirmed he holds Bencho Pro and has the Bencho connector attached; Pro blocks may be used. This answers the open question above.
- Mistake recorded: Claude committed an agent worktree folder as an embedded repository (`9ef7e61`) and removed it in the next commit (`c7f92ed`), adding `.claude/` to `.gitignore`.
