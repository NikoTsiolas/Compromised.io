"""Action lines from rules: the action a source states in a structured field.

CISA's Known Exploited Vulnerabilities catalog gives every entry a required action. Its adapter
(#4) puts that field in the record's metadata under ``required_action``; the first sentence
becomes the action line, shortened at a clause boundary when long. Nothing else produces an
action line by rule: without a stated action there is none.
"""

import re

from compromised.records import SourceRecord

ACTION_LIMIT = 160
SENTENCE_END = re.compile(r"(?<=[.!?])\s")


def required_action_line(records: list[SourceRecord]) -> str | None:
    for record in records:
        value = record.metadata.get("required_action")
        if isinstance(value, str) and value.strip():
            return first_sentence(value)
    return None


def first_sentence(text: str, limit: int = ACTION_LIMIT) -> str:
    sentence = SENTENCE_END.split(" ".join(text.split()), maxsplit=1)[0]
    if len(sentence) <= limit:
        return sentence
    head = sentence[: limit - 1]
    for boundary in (", ", "; ", " "):
        if boundary in head:
            return head[: head.rindex(boundary)].rstrip(" ,;:") + "."
    return head + "."
