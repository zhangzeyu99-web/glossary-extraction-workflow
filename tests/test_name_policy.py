from __future__ import annotations

from glossary_extraction.constants import CATEGORY_LABELS
from glossary_extraction.heuristics import category_for
from glossary_extraction.models import Record
from glossary_extraction.name_policy import classify_term_type


def test_skill_name_uses_explicit_field_or_id_context():
    records = [
        Record(
            "SkillName_1001",
            "鲨潮护盾",
            "Sharkguard",
            sheet_name="技能",
            row_number=2,
            source_field="中文",
            term_type_hint="技能名",
        ),
        Record(
            "SkillDesc_1001",
            "召唤鲨潮并获得护盾",
            "Summons a shark tide and gains a shield.",
            sheet_name="技能",
            row_number=3,
            source_field="中文",
        ),
    ]

    decision = classify_term_type("鲨潮护盾", [0], records, {})

    assert decision.term_type == "ui_skill_name"
    assert decision.category == "技能名"
    assert decision.bypass_frequency is True
    assert decision.needs_review is False


def test_location_name_uses_explicit_context():
    records = [
        Record(
            "MapName_2001",
            "暮色海岸",
            "Dusk Coast",
            sheet_name="地图名称",
            row_number=2,
            source_field="中文",
        )
    ]

    decision = classify_term_type("暮色海岸", [0], records, {})

    assert decision.term_type == "location_name"
    assert decision.category == "地名"
    assert decision.bypass_frequency is True


def test_four_character_text_is_not_a_skill_without_context():
    records = [Record("Text_1", "终极挑战", "Final Challenge")]

    decision = classify_term_type("终极挑战", [0], records, {})

    assert decision.term_type == "atomic"
    assert decision.bypass_frequency is False


def test_conflicting_explicit_signals_require_review():
    records = [
        Record(
            "MapName_2001",
            "暮色海岸",
            "Dusk Coast",
            sheet_name="地图",
            term_type_hint="技能名",
        )
    ]

    decision = classify_term_type("暮色海岸", [0], records, {})

    assert decision.term_type == "needs_review"
    assert decision.needs_review is True


def test_category_for_maps_to_one_delivery_category():
    assert CATEGORY_LABELS[category_for("红色品质")] == "品质"
    assert CATEGORY_LABELS[category_for("公会")] == "联盟"
    assert CATEGORY_LABELS[category_for("火焰技能")] == "技能"
    assert CATEGORY_LABELS[category_for("无法判断的文本")] == "待确认"
