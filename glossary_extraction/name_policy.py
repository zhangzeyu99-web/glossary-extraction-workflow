"""Proper-name classification and UI naming policies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from glossary_extraction.models import Record


PROPER_NAME_TYPES = frozenset({"ui_skill_name", "location_name"})
VALID_TERM_TYPES = frozenset({"atomic", "ui_skill_name", "location_name", "needs_review"})

SKILL_HINTS = (
    "技能名",
    "skill_name",
    "skillname",
    "ability_name",
    "abilityname",
)
LOCATION_HINTS = (
    "地名",
    "地点名",
    "场景名",
    "地图名",
    "location_name",
    "locationname",
    "map_name",
    "mapname",
    "scene_name",
    "scenename",
)


@dataclass(frozen=True)
class TermTypeDecision:
    term_type: str
    category: str
    confidence: str
    evidence: tuple[str, ...]
    bypass_frequency: bool
    needs_review: bool


def normalized_context(record: Record) -> str:
    return " ".join(
        str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
        for value in (
            record.term_type_hint,
            record.sheet_name,
            record.source_field,
            record.row_id,
        )
        if str(value or "").strip()
    )


def classify_term_type(
    term: str,
    exact_record_indexes: list[int],
    records: list[Record],
    curated_state: dict[str, Any],
) -> TermTypeDecision:
    del term
    override = str(curated_state.get("term_type_override") or "").strip().lower()
    if override in VALID_TERM_TYPES:
        category = {
            "ui_skill_name": "技能名",
            "location_name": "地名",
            "needs_review": "待确认",
        }.get(override, "")
        return TermTypeDecision(
            term_type=override,
            category=category,
            confidence="high",
            evidence=(f"curated:{override}",),
            bypass_frequency=override in PROPER_NAME_TYPES,
            needs_review=override == "needs_review",
        )

    evidence: list[str] = []
    has_skill = False
    has_location = False
    for index in exact_record_indexes:
        context = normalized_context(records[index])
        if any(hint in context for hint in SKILL_HINTS):
            has_skill = True
            evidence.append(f"skill_context:{records[index].row_id}")
        if any(hint in context for hint in LOCATION_HINTS):
            has_location = True
            evidence.append(f"location_context:{records[index].row_id}")

    if has_skill and has_location:
        return TermTypeDecision("needs_review", "待确认", "low", tuple(evidence), False, True)
    if has_skill:
        return TermTypeDecision("ui_skill_name", "技能名", "high", tuple(evidence), True, False)
    if has_location:
        return TermTypeDecision("location_name", "地名", "high", tuple(evidence), True, False)
    return TermTypeDecision("atomic", "", "medium", tuple(), False, False)
