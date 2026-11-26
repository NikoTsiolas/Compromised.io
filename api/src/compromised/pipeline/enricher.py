"""Enricher (#8): one Claude Haiku call per new event, with the rule classifier as fallback.

What the model sees: the event's earliest headline and excerpt, wrapped and marked as untrusted
data (``UntrustedItem``; nothing else crosses the ``ModelClient`` interface).

What it may return (``Reply``, validated, length-limited, reduced to plain text): a category,
the affected organization, whether the item is commentary, a one-to-two sentence summary, and an
action line with the words of the input that state it. Anything else, an extra field included,
rejects the whole reply.

What it may change: the category and commentary flag, and the organization only when the rules
found none and the input names it. The action line is kept only when its quote appears in the
input. Verification status and score (#7) are not in the reply and never written here.

When the model is unavailable, no key is configured, the reply is rejected, or the daily cap is
reached, the event keeps its rule-based facts and stays ``awaiting``; ``enrich_pending`` retries
awaiting events on a later pass. Ingestion never waits on, or fails because of, the model.
"""

import json
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from typing import Annotated, Literal, Protocol

import psycopg
from pydantic import BaseModel, ConfigDict, StringConstraints, ValidationError

from compromised import catalog, storage
from compromised.pipeline import classifier, scope
from compromised.pipeline.classifier import CATEGORIES
from compromised.pipeline.normalizer import plain_text

log = logging.getLogger("compromised.enricher")

DEFAULT_DAILY_CAP = 500
MAX_REJECTED_REPLIES = 3  # an event whose replies keep failing validation stops being retried

SUMMARY_LIMIT = 320
ACTION_LIMIT = 160
ORGANIZATION_LIMIT = 80
QUOTE_LIMIT = 300

# Links have no place in a summary or action line; text that carries one is refused.
LINK = re.compile(r"https?://|\bwww\.|\.onion\b|\bhxxps?\b", re.IGNORECASE)
# Advice must never send a reader somewhere: an action line naming a domain or an email address
# is refused ("Update Windows now" needs neither). Summaries may name a company's domain.
PLACE = re.compile(r"[\w-]+\.[a-z]{2,}\b|@", re.IGNORECASE)


@dataclass(frozen=True)
class UntrustedItem:
    """Everything the model is given about an event. Feed text: data, never instructions."""

    headline: str
    excerpt: str


class ModelUnavailable(Exception):
    """The model could not be reached or gave no usable answer (outage, rate limit, refusal)."""


class ModelDeclined(Exception):
    """The model answered without a usable reply (refusal, cut off). Counts as a rejected reply."""


class ModelClient(Protocol):
    def complete(self, item: UntrustedItem) -> str:
        """The model's raw reply (JSON text) for one item.

        Raises ModelUnavailable when it cannot be reached, ModelDeclined when it gave no reply.
        """


def _text(limit: int):
    return Annotated[str, StringConstraints(strip_whitespace=True, max_length=limit)]


class Reply(BaseModel):
    """The only shape a model reply may have."""

    model_config = ConfigDict(extra="forbid", strict=True)

    category: Literal[tuple(CATEGORIES)]  # type: ignore[valid-type]
    affected_organization: _text(ORGANIZATION_LIMIT) | None
    commentary: bool
    summary: _text(SUMMARY_LIMIT)
    action_line: _text(ACTION_LIMIT) | None
    action_quote: _text(QUOTE_LIMIT) | None


# The schema sent to the API with the request. Length limits are enforced by ``Reply`` here,
# since structured outputs do not accept string-length constraints.
_NULLABLE_STRING = {"anyOf": [{"type": "string"}, {"type": "null"}]}
REPLY_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": list(CATEGORIES)},
        "affected_organization": _NULLABLE_STRING,
        "commentary": {"type": "boolean"},
        "summary": {"type": "string"},
        "action_line": _NULLABLE_STRING,
        "action_quote": _NULLABLE_STRING,
    },
    "required": [
        "category",
        "affected_organization",
        "commentary",
        "summary",
        "action_line",
        "action_quote",
    ],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class Enrichment:
    """A checked reply, as stored."""

    category: str
    commentary: bool
    organization: str | None
    summary: str
    action_line: str | None


class Rejected(ValueError):
    pass


def check(raw: str, item: UntrustedItem) -> Enrichment:
    """Validate a raw reply against the schema and the input. Raises Rejected."""
    try:
        reply = Reply.model_validate(json.loads(raw))
    except (ValueError, TypeError, ValidationError) as exc:  # JSONDecodeError is a ValueError
        raise Rejected(f"reply does not match the schema: {type(exc).__name__}") from None
    summary = plain_text(reply.summary)
    if not summary:
        raise Rejected("empty summary")
    if LINK.search(summary):
        raise Rejected("summary contains a link")
    source_text = _comparable(f"{item.headline} {item.excerpt}")
    return Enrichment(
        category=reply.category,
        commentary=reply.commentary,
        organization=_named_in_input(reply.affected_organization, source_text),
        summary=summary,
        action_line=_stated_action(reply.action_line, reply.action_quote, source_text),
    )


def _comparable(text: str) -> str:
    return " ".join(plain_text(text).casefold().split())


def _named_in_input(name: str | None, source_text: str) -> str | None:
    """The organization, only if the input names it and it is not a reporter or attacker."""
    name = plain_text(name or "")
    if not name or name.casefold() == "unknown" or catalog.load().is_not_organization(name):
        return None
    pattern = rf"(?<!\w){re.escape(_comparable(name))}(?!\w)"
    return name if re.search(pattern, source_text) else None


def _stated_action(line: str | None, quote: str | None, source_text: str) -> str | None:
    """The action line, only if its supporting quote appears word for word in the input."""
    line = plain_text(line or "")
    quote = _comparable(quote or "")
    if not line or not quote or LINK.search(line) or PLACE.search(line):
        return None
    if quote not in source_text:
        return None
    return line


# Outcomes after which no further event is tried in the same pass: the cap is reached, or the
# model is down and the next call would most likely fail too.
STOP_THE_PASS = frozenset({"capped", "unavailable"})


@dataclass(frozen=True)
class Outcome:
    enriched: bool
    reason: str  # enriched | capped | unavailable | rejected | gone


class Enricher:
    def __init__(
        self,
        client: ModelClient,
        *,
        daily_cap: int = DEFAULT_DAILY_CAP,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ):
        self.client = client
        self.daily_cap = daily_cap
        self.clock = clock

    def enrich(self, conn: psycopg.Connection, event_id: int) -> Outcome:
        """Enrich one event. Never raises because of the model; failures leave it awaiting."""
        records = storage.event_records(conn, event_id)
        if not records:
            return Outcome(False, "gone")
        lead = records[0]
        item = UntrustedItem(headline=lead.headline, excerpt=lead.excerpt)
        now = self.clock()
        if not storage.take_enrichment_call(conn, _utc_day(now), self.daily_cap):
            return Outcome(False, "capped")
        try:
            raw = self.client.complete(item)
        except ModelDeclined as exc:
            raw = None
            declined = str(exc)
        except ModelUnavailable as exc:  # outage, timeout, rate limit: rules stay in place
            log.warning("model unavailable", extra={"event_id": event_id, "error": str(exc)})
            return Outcome(False, "unavailable")
        except Exception:  # a fault in the client must not stop ingestion either
            log.exception("model client failed", extra={"event_id": event_id})
            return Outcome(False, "unavailable")
        try:
            if raw is None:
                raise Rejected(f"model declined: {declined}")
            enrichment = check(raw, item)
            if _attacker_claim(lead):
                # The model read an attacker's words: never keep advice drawn from them, not
                # even once a press story joins the event and it stops being claim-only.
                enrichment = replace(enrichment, action_line=None)
        except Rejected as exc:
            storage.record_rejected_enrichment(conn, event_id)
            log.warning("model reply rejected", extra={"event_id": event_id, "error": str(exc)})
            return Outcome(False, "rejected")
        with conn.transaction():
            storage.save_enrichment(conn, event_id, enrichment, at=now)
            scope.refresh_event(conn, event_id)
        return Outcome(True, "enriched")

    def enrich_pending(self, conn: psycopg.Connection, *, limit: int = 50) -> list[Outcome]:
        """Enrich events still awaiting enrichment, newest first, until the cap is reached."""
        outcomes = []
        for event_id in storage.awaiting_enrichment(conn, limit, MAX_REJECTED_REPLIES):
            outcome = self.enrich(conn, event_id)
            outcomes.append(outcome)
            if outcome.reason in STOP_THE_PASS:
                break
        return outcomes


def _attacker_claim(record) -> bool:
    return classifier.source_prior(record.source_id) == "claim" or bool(
        (record.metadata or {}).get("attacker_claim")
    )


def _utc_day(moment: datetime) -> date:
    return moment.astimezone(UTC).date()
