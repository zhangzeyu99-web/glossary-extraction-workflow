# 专名提取与译文权威修复 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Execution authorization:** 用户已于 2026-07-24 明确要求执行、校验并推送。

**Implementation status:** 已完成代码、测试与文档实施；最终验证和远端推送记录见对应提交与 PR。

**Goal:** 让术语提取稳定识别低频技能名和地名，明确当前语言表与历史术语的译文优先级，并在交付前发现名称过长、过度压缩和项目内重名。

**Architecture:** 在现有普通术语通道旁增加专名判定与名称检查层。Excel 读取阶段只保留判断所需的表名、字段名、行号和显式类型；提取阶段先判定类型，再决定是否绕过频次门槛；译文阶段把当前语言表作为主证据，历史术语和观察记录只用于补空与告警；正式交付表保持干净，详细证据留在内部检查表和精简 AI 检查包。

**Tech Stack:** Python 3.11+、openpyxl、dataclasses、unittest/pytest、现有 JSON fixture harness。

## Global Constraints

- 只修改 `D:\codex\glossary-extraction-workflow`。
- 不修改或同步 `D:\codex\localization-workflow-studio`。
- 不修改、不暂存现有未提交文件 `data/experience/observed_terms.json`。
- 频次只用于排序和取证，不得再次成为技能名、地名等专名的准入条件。
- 不根据“四字中文”或中文长度推断技能名、地名。
- 当前语言表存在非空译文时，当前译文优先；历史术语和观察记录不得静默覆盖。
- 英语技能名建议不超过 2 个词和 24 个字符；英语地名建议不超过 2 个核心词和 28 个字符。超限默认是警告，不得机械截断。
- 非英语名称不机械套用英语词数，只进入语义单位和自然度人工检查。
- 正式交付默认只保留 `ID / CN / 目标语言主译 / 分类`；审计信息只进入详细工作簿或精简检查包。
- 原有术语表补充场景必须保留原行、原顺序，只追加去重后的新增项。
- 本计划不更新 `README.md`、`VERSION`、`CHANGELOG.md`，不提交、不推送；这些动作必须由用户另行明确授权。

---

### Task 1: 保留专名判断所需的行上下文

**Files:**
- Modify: `glossary_extraction/models.py`
- Modify: `glossary_extraction/constants.py`
- Modify: `glossary_extraction/excel_io.py:160-203`
- Modify: `glossary_extraction/excel_io.py:406-438`
- Test: `tests/test_extract_glossary_workflow.py`

**Interfaces:**
- Consumes: 现有 `Record(row_id, source, target)` 调用。
- Produces: 向后兼容的 `Record`，新增 `sheet_name`、`row_number`、`source_field`、`term_type_hint`。
- Produces: `AUTO_TERM_TYPE_HEADERS`，用于读取 `术语类型 / 类型 / 分类 / term_type`。

- [ ] **Step 1: 写入失败测试，证明显式类型和表结构上下文会被保留**

```python
def test_records_from_rows_preserves_term_type_context(self):
    rows = [
        ["ID", "中文", "英文", "术语类型"],
        ["SkillName_1001", "鲨潮护盾", "Sharkguard", "技能名"],
        ["MapName_2001", "暮色海岸", "Dusk Coast", "地名"],
    ]

    records = MODULE.records_from_rows(
        rows=rows,
        sheet_title="技能与地图",
        id_column="ID",
        source_column="中文",
        target_column="英文",
    )

    self.assertEqual(records[0].sheet_name, "技能与地图")
    self.assertEqual(records[0].row_number, 2)
    self.assertEqual(records[0].source_field, "中文")
    self.assertEqual(records[0].term_type_hint, "技能名")
    self.assertEqual(records[1].term_type_hint, "地名")
```

- [ ] **Step 2: 运行测试并确认旧模型缺少字段**

Run:

```powershell
python -m pytest tests/test_extract_glossary_workflow.py::GlossaryWorkflowTests::test_records_from_rows_preserves_term_type_context -q
```

Expected: FAIL，错误包含 `Record` 没有 `sheet_name` 或 `term_type_hint`。

- [ ] **Step 3: 扩展 `Record`，保持旧的三个位置参数可用**

```python
@dataclass
class Record:
    row_id: str
    source: str
    target: str
    sheet_name: str = ""
    row_number: int = 0
    source_field: str = ""
    term_type_hint: str = ""
```

- [ ] **Step 4: 增加类型字段表头并在两条 Excel 读取路径中赋值**

```python
AUTO_TERM_TYPE_HEADERS = [
    "term_type",
    "术语类型",
    "名称类型",
    "类型",
    "分类",
]
```

在 `records_from_rows` 中从实际表头行读取字段：

```python
header_row_index = layout.header_row_index if layout is not None else 0
actual_headers = list(rows[header_row_index])
source_field = clean_text(value_at(actual_headers, source_index))
term_type_index = first_matching_header_fuzzy(actual_headers, AUTO_TERM_TYPE_HEADERS)

term_type_hint = clean_text(value_at(row_values, term_type_index))
records.append(
    Record(
        row_id=row_id,
        source=source,
        target=target,
        sheet_name=sheet_title,
        row_number=row_number,
        source_field=source_field,
        term_type_hint=term_type_hint,
    )
)
```

在 `auto_records_from_sheet_rows` 中使用相同规则；没有类型列时写空字符串，不猜测。

- [ ] **Step 5: 运行读取层测试**

Run:

```powershell
python -m pytest tests/test_extract_glossary_workflow.py -q
```

Expected: PASS，现有所有 `Record("1", "报名", "Sign Up")` 调用保持兼容。

- [ ] **Step 6: 提交本任务**

```powershell
git add glossary_extraction/models.py glossary_extraction/constants.py glossary_extraction/excel_io.py tests/test_extract_glossary_workflow.py
git commit -m "feat: retain term classification context"
```

---

### Task 2: 增加技能名、地名的显式分类器

**Files:**
- Create: `glossary_extraction/name_policy.py`
- Modify: `glossary_extraction/experience.py:26-176`
- Modify: `glossary_extraction/constants.py:369-378`
- Modify: `glossary_extraction/heuristics.py:249-270`
- Test: `tests/test_name_policy.py`

**Interfaces:**
- Consumes: `term: str`、该术语的准确命中行下标、完整 `records`、curated term state。
- Produces: `TermTypeDecision(term_type, category, confidence, evidence, bypass_frequency, needs_review)`。
- Produces: `classify_term_type(term, exact_record_indexes, records, curated_state) -> TermTypeDecision`。
- Curated state 新增可选字段：`term_type_override`，合法值为 `atomic / ui_skill_name / location_name / needs_review`。

- [ ] **Step 1: 为明确技能名、明确地名、普通短词和冲突证据写失败测试**

```python
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
```

- [ ] **Step 2: 运行测试并确认模块不存在**

Run:

```powershell
python -m pytest tests/test_name_policy.py -q
```

Expected: FAIL，错误包含 `No module named 'glossary_extraction.name_policy'`。

- [ ] **Step 3: 实现只依赖明确上下文的分类器**

```python
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
    override = clean_text(curated_state.get("term_type_override")).lower()
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
```

实现时不得把 `len(term) == 4`、`len(term) <= 6` 或其他中文长度条件加入分类器。

- [ ] **Step 4: 给 curated state 增加类型覆盖字段并保持旧 JSON 兼容**

```python
def default_curated_term_state() -> dict[str, Any]:
    return {
        "approved_en": "",
        "approved_en2": "",
        "block_en2": False,
        "ignore": False,
        "note": "",
        "category_override": "",
        "term_type_override": "",
    }
```

`split_legacy_term_memory`、`get_curated_term_state` 和 `sanitize_curated_rules` 都必须读取并保留 `term_type_override`；旧文件缺失该字段时自动使用空字符串。

- [ ] **Step 5: 把分类映射改成单一类别，并增加技能名、地名**

```python
CATEGORY_LABELS = {
    "rarity": "品质",
    "resource": "资源",
    "stat": "属性",
    "action": "动作",
    "activity": "活动",
    "ui": "UI",
    "equipment": "装备",
    "item": "道具",
    "skill": "技能",
    "emblem": "纹章",
    "dungeon": "副本",
    "alliance": "联盟",
    "hero": "英雄",
    "monster": "怪物",
    "pet": "宠物",
    "world": "世界观",
    "mail": "邮件",
    "ui_skill_name": "技能名",
    "location_name": "地名",
    "needs_review": "待确认",
}
```

同步把 `category_for` 改成只返回单一分类代码：

```python
def category_for(term: str) -> str:
    if term in RARITY_TERMS or any(key in term for key in ("品质", "稀有度")):
        return "rarity"
    if term in RESOURCE_TERMS:
        return "resource"
    if term in STAT_TERMS or any(key in term for key in ("伤害", "攻击", "生命", "防御", "暴击")):
        return "stat"
    if term in ACTION_TERMS:
        return "action"
    if "活动" in term:
        return "activity"
    if any(key in term for key in ("邮件", "信件")):
        return "mail"
    if any(key in term for key in ("公会", "联盟")):
        return "alliance"
    if any(key in term for key in ("副本", "秘境")):
        return "dungeon"
    if any(key in term for key in ("英雄", "角色", "职业")):
        return "hero"
    if any(key in term for key in ("怪物", "首领", "BOSS", "Boss", "boss")):
        return "monster"
    if "宠物" in term:
        return "pet"
    if any(key in term for key in ("武器", "装备", "护甲")):
        return "equipment"
    if any(key in term for key in ("道具", "宝箱", "药水")):
        return "item"
    if "技能" in term:
        return "skill"
    if any(key in term for key in ("纹章", "铭文", "宝石")):
        return "emblem"
    if term in SYSTEM_TERMS:
        return "ui"
    if term in OBJECT_TERMS:
        return "item"
    if term in STATUS_TERMS:
        return "ui"
    return "needs_review"
```

分类结果必须通过 `CATEGORY_LABELS` 转成一个中文主分类，不能再输出 `资源/货币/奖励` 等复合标签。

增加断言：

```python
def test_category_for_maps_to_one_delivery_category():
    assert CATEGORY_LABELS[category_for("红色品质")] == "品质"
    assert CATEGORY_LABELS[category_for("公会")] == "联盟"
    assert CATEGORY_LABELS[category_for("火焰技能")] == "技能"
    assert CATEGORY_LABELS[category_for("无法判断的文本")] == "待确认"
```

- [ ] **Step 6: 运行分类器和经验层测试**

Run:

```powershell
python -m pytest tests/test_name_policy.py tests/test_extract_glossary_workflow.py -q
```

Expected: PASS。

- [ ] **Step 7: 提交本任务**

```powershell
git add glossary_extraction/name_policy.py glossary_extraction/experience.py glossary_extraction/constants.py glossary_extraction/heuristics.py tests/test_name_policy.py
git commit -m "feat: classify skill and location names"
```

---

### Task 3: 让低频专名绕过普通术语频次门槛

**Files:**
- Modify: `glossary_extraction/heuristics.py:351-520`
- Modify: `glossary_extraction/reporting.py`
- Test: `tests/test_extract_glossary_workflow.py`
- Create: `fixtures/proper_name_extraction_regression.json`
- Modify: `scripts/run_glossary_harness.py:214-295`
- Modify: `tests/test_glossary_harness.py`

**Interfaces:**
- Consumes: Task 2 的 `classify_term_type` 和 `TermTypeDecision`。
- Produces: 每个候选新增 `TermType`、`TypeConfidence`、`TypeEvidence`、`NeedsReview`。
- Produces: 明确技能名、地名即使 `HitRows == 1` 也进入交付候选；`needs_review` 只进入详细表和高风险表，不进入正式交付。

- [ ] **Step 1: 写失败测试，复现 `min_hit=5` 丢失单次技能名**

```python
def test_singleton_proper_names_bypass_frequency_threshold(self):
    records = [
        MODULE.Record(
            "SkillName_1001",
            "鲨潮护盾",
            "Sharkguard",
            sheet_name="技能名称",
            row_number=2,
        ),
        MODULE.Record(
            "MapName_2001",
            "暮色海岸",
            "Dusk Coast",
            sheet_name="地图名称",
            row_number=3,
        ),
        MODULE.Record("Text_1", "普通文本", "Normal Text"),
    ]

    all_rows, glossary_rows, high_risk_rows, _manual_rows, final_rows = MODULE.build_term_rows(
        records=records,
        min_hit=5,
        glossary_hit_threshold=10,
        curated_rules=MODULE.new_curated_rules(),
        observations_store=MODULE.new_observation_store(),
        input_digest="singleton-proper-names",
    )

    final = {row["CN"]: row for row in final_rows}
    assert final["鲨潮护盾"]["Category"] == "技能名"
    assert final["鲨潮护盾"]["HitRows"] == 1
    assert final["暮色海岸"]["Category"] == "地名"
    assert "普通文本" not in final
```

再增加一条冲突类型测试，断言 `NeedsReview == "Yes"` 且不进入 `final_rows`。

- [ ] **Step 2: 运行聚焦测试并确认技能名被旧频次门槛过滤**

Run:

```powershell
python -m pytest tests/test_extract_glossary_workflow.py::GlossaryWorkflowTests::test_singleton_proper_names_bypass_frequency_threshold -q
```

Expected: FAIL，`鲨潮护盾` 不在 `final_rows`。

- [ ] **Step 3: 在统计频次前建立准确命中行索引**

```python
exact_record_indexes: dict[str, list[int]] = defaultdict(list)
for index, record in enumerate(records):
    if is_valid_term(record.source):
        label_counter[record.source] += 1
        exact_record_indexes[record.source].append(index)
        if record.target:
            label_translations[record.source][record.target] += 1
```

- [ ] **Step 4: 在 `hits < min_hit` 前完成类型判定**

```python
curated_state = experience.get_curated_term_state(curated_rules, term, create=False)
type_decision = classify_term_type(
    term=term,
    exact_record_indexes=exact_record_indexes[term],
    records=records,
    curated_state=curated_state,
)

if hits < min_hit and not type_decision.bypass_frequency and not type_decision.needs_review:
    continue
```

候选行增加：

```python
category_override = clean_text(curated_state.get("category_override"))
category = (
    type_decision.category
    or category_override
    or CATEGORY_LABELS[category_for(term)]
)
needs_review = type_decision.needs_review or category == "待确认"

"TermType": type_decision.term_type,
"TypeConfidence": type_decision.confidence,
"TypeEvidence": " | ".join(type_decision.evidence),
"NeedsReview": "Yes" if needs_review else "No",
"Category": category,
```

- [ ] **Step 5: 修正正式术语准入规则**

```python
glossary_rows = [
    row
    for row in rows_by_term
    if row["NeedsReview"] != "Yes"
    and (
        int(row["HitRows"]) >= glossary_hit_threshold
        or row["Risk"] == "high"
        or row["TermType"] in PROPER_NAME_TYPES
    )
]
high_risk_rows = [
    row
    for row in rows_by_term
    if row["Risk"] == "high" or row["NeedsReview"] == "Yes"
]
```

`needs_review` 不得因为旧的 `Risk == "high"` 条件进入正式交付。

- [ ] **Step 6: 扩展 harness 比较分类和术语类型**

`scripts/run_glossary_harness.py` 的 `expected_final` 比较改为检查 CN 以外的所有显式期望字段：

```python
field_mismatches: dict[str, dict[str, object]] = {}
for field, expected_value in expected_item.items():
    if field == "CN":
        continue
    actual_value = predicted.get(field, "")
    if actual_value != expected_value:
        field_mismatches[field] = {
            "expected": expected_value,
            "actual": actual_value,
        }
if field_mismatches:
    mismatched_terms.append({"CN": term, "fields": field_mismatches})
```

新 fixture 至少包含：

```json
{
  "sheet": "Names",
  "columns": {"id": "ID", "source": "cn", "target": "en", "term_type": "术语类型"},
  "extract": {"min_hit": 5, "glossary_hit_threshold": 10},
  "rows": [
    {"ID": "SkillName_1001", "cn": "鲨潮护盾", "en": "Sharkguard", "术语类型": "技能名"},
    {"ID": "MapName_2001", "cn": "暮色海岸", "en": "Dusk Coast", "术语类型": "地名"},
    {"ID": "Text_1", "cn": "普通文本", "en": "Normal Text", "术语类型": ""}
  ],
  "expected_final": [
    {"CN": "鲨潮护盾", "EN": "Sharkguard", "Category": "技能名", "TermType": "ui_skill_name"},
    {"CN": "暮色海岸", "EN": "Dusk Coast", "Category": "地名", "TermType": "location_name"}
  ],
  "expected_absent": ["普通文本"],
  "strict_terms": true
}
```

`write_fixture_workbook` 必须按 fixture 的可选 `term_type` 列写入，不能把类型信息只放在测试代码中：

```python
column_keys = ["id", "source", "target"]
if columns.get("term_type"):
    column_keys.append("term_type")
worksheet.append([columns[key] for key in column_keys])
for row in fixture["rows"]:
    worksheet.append([row.get(columns[key], "") for key in column_keys])
```

- [ ] **Step 7: 运行聚焦测试与新 fixture**

Run:

```powershell
python -m pytest tests/test_extract_glossary_workflow.py tests/test_glossary_harness.py -q
python scripts/run_glossary_harness.py fixtures/proper_name_extraction_regression.json
```

Expected: PASS；fixture 报告 `coverage: 1.0`、`missing_terms: []`、`unexpected_terms: []`。

- [ ] **Step 8: 提交本任务**

```powershell
git add glossary_extraction/heuristics.py glossary_extraction/reporting.py scripts/run_glossary_harness.py tests/test_extract_glossary_workflow.py tests/test_glossary_harness.py fixtures/proper_name_extraction_regression.json
git commit -m "fix: retain low-frequency proper names"
```

---

### Task 4: 修正当前译文与历史译文的优先级

**Files:**
- Modify: `glossary_extraction/experience.py:277-311`
- Modify: `glossary_extraction/heuristics.py:388-499`
- Modify: `glossary_extraction/announcement.py:74-95`
- Test: `tests/test_extract_glossary_workflow.py`
- Create: `fixtures/current_translation_authority_regression.json`

**Interfaces:**
- Consumes: 当前运行从语言表提取出的 `exact_translation_counter`、curated state、observation state。
- Produces: `TranslationSource`，值为 `current_table / curated / none`。
- Produces: `TranslationConflict` 和 `TranslationConflictValues`。
- 保证: 当前语言表非空译文优先；curated 只补当前空值；observation 只作证据和告警，不直接成为正式主译。

- [ ] **Step 1: 把旧的“curated 总是覆盖”测试改成两条明确规则**

```python
def test_current_language_table_translation_wins_over_curated(self):
    curated = {
        "version": 1,
        "terms": {
            "报名": {
                "approved_en": "Registration",
                "approved_en2": "",
                "block_en2": True,
                "ignore": False,
                "note": "",
                "category_override": "",
                "term_type_override": "",
            }
        },
    }
    records = [MODULE.Record("1", "报名", "Sign Up")]

    _all, _glossary, _risk, _manual, final = MODULE.build_term_rows(
        records=records,
        min_hit=1,
        glossary_hit_threshold=1,
        curated_rules=curated,
        observations_store=MODULE.new_observation_store(),
        input_digest="current-wins",
    )

    row = final[0]
    self.assertEqual(row["EN"], "Sign Up")
    self.assertEqual(row["TranslationSource"], "current_table")
    self.assertEqual(row["TranslationConflict"], "Yes")
    self.assertIn("Registration", row["TranslationConflictValues"])


def test_curated_translation_only_fills_blank_current_translation(self):
    curated = {
        "version": 1,
        "terms": {
            "报名": {
                "approved_en": "Registration",
                "approved_en2": "",
                "block_en2": True,
                "ignore": False,
                "note": "",
                "category_override": "",
                "term_type_override": "",
            }
        },
    }
    records = [MODULE.Record("1", "报名", "")]

    _all, _glossary, _risk, _manual, final = MODULE.build_term_rows(
        records=records,
        min_hit=1,
        glossary_hit_threshold=1,
        curated_rules=curated,
        observations_store=MODULE.new_observation_store(),
        input_digest="curated-fills-blank",
        include_empty_final_terms=True,
    )

    self.assertEqual(final[0]["EN"], "Registration")
    self.assertEqual(final[0]["TranslationSource"], "curated")
```

增加公告测试：当前公告语言表为 `Sign Up`、curated 为 `Registration` 时，公告 `Glossary` 必须输出 `Sign Up`。

- [ ] **Step 2: 运行测试并确认旧代码选择 `approved_en`**

Run:

```powershell
python -m pytest tests/test_extract_glossary_workflow.py -q
```

Expected: FAIL，实际 EN 为 `Registration`。

- [ ] **Step 3: 把主译选择和历史计数合并拆开**

新增纯函数：

```python
def choose_primary_translation(
    current_counter: Counter[str],
    curated_state: dict[str, Any],
) -> tuple[str, str, list[str]]:
    current = current_counter.most_common(1)[0][0] if current_counter else ""
    approved = clean_text(curated_state.get("approved_en"))
    conflicts = [approved] if current and approved and approved != current else []
    if current:
        return current, "current_table", conflicts
    if approved:
        return approved, "curated", []
    return "", "none", []
```

`build_term_rows` 必须先使用当前运行的 `exact_translations` 选择主译，再把 observation history 合并到审计计数中。历史计数不得反向改变已经选择的主译。

候选行增加：

```python
"TranslationSource": translation_source,
"TranslationConflict": "Yes" if translation_conflicts else "No",
"TranslationConflictValues": " | ".join(translation_conflicts),
```

- [ ] **Step 4: 修改 curated preference，使其不再覆盖非空当前译文**

`apply_curated_preferences` 改成只处理 EN2、ignore、note 等明确规则；主 EN 由 `choose_primary_translation` 决定。删除以下旧行为：

```python
if approved_en:
    suggested_en = approved_en
    example_en = approved_en
```

保留 `block_en2` 和明确 `approved_en2` 逻辑。

- [ ] **Step 5: 修改公告 lookup 的同类优先级**

把：

```python
en = approved_en or common_en
```

改成：

```python
en = common_en or approved_en
```

并在内部统计中记录 `current_curated_conflicts`，正式 `Glossary` 仍保持干净。

- [ ] **Step 6: 增加译文权威 fixture**

`fixtures/current_translation_authority_regression.json` 使用以下结构：

```json
{
  "sheet": "Sheet0",
  "columns": {"id": "ID", "source": "cn", "target": "en"},
  "extract": {"min_hit": 1, "glossary_hit_threshold": 1},
  "curated_rules": {
    "version": 1,
    "terms": {
      "报名": {
        "approved_en": "Registration",
        "approved_en2": "",
        "block_en2": true,
        "ignore": false,
        "note": "",
        "category_override": "UI",
        "term_type_override": ""
      },
      "旧港": {
        "approved_en": "Old Harbor",
        "approved_en2": "",
        "block_en2": true,
        "ignore": false,
        "note": "",
        "category_override": "地名",
        "term_type_override": "location_name"
      }
    }
  },
  "observations_store": {
    "version": 1,
    "terms": {
      "报名": {
        "observed_exact_candidates": {"Registration": 8},
        "observed_example_usages": {},
        "observed_manual_adaptations": {},
        "seen_runs": 4,
        "last_seen_at": "2026-07-01T00:00:00+00:00",
        "last_input_digest": "old"
      }
    }
  },
  "rows": [
    {"ID": "1", "cn": "报名", "en": "Sign Up"},
    {"ID": "2", "cn": "旧港", "en": ""}
  ],
  "expected_final": [
    {
      "CN": "报名",
      "EN": "Sign Up",
      "TranslationSource": "current_table",
      "TranslationConflict": "Yes"
    },
    {
      "CN": "旧港",
      "EN": "Old Harbor",
      "TermType": "location_name",
      "TranslationSource": "curated",
      "TranslationConflict": "No"
    }
  ],
  "expected_absent": [],
  "strict_terms": true
}
```

- [ ] **Step 7: 运行译文优先级回归**

Run:

```powershell
python -m pytest tests/test_extract_glossary_workflow.py tests/test_glossary_harness.py -q
python scripts/run_glossary_harness.py fixtures/current_translation_authority_regression.json
```

Expected: PASS；当前译文均胜出，空译文才由 curated 补齐。

- [ ] **Step 8: 提交本任务**

```powershell
git add glossary_extraction/experience.py glossary_extraction/heuristics.py glossary_extraction/announcement.py tests/test_extract_glossary_workflow.py fixtures/current_translation_authority_regression.json
git commit -m "fix: prefer current language-table translations"
```

---

### Task 5: 增加名称长度、重名和 AI 精简检查包

**Files:**
- Modify: `glossary_extraction/name_policy.py`
- Modify: `glossary_extraction/heuristics.py:472-499`
- Modify: `glossary_extraction/cli.py:147-281`
- Modify: `glossary_extraction/cli.py:694-715`
- Modify: `glossary_extraction/excel_io.py:655-729`
- Test: `tests/test_name_policy.py`
- Test: `tests/test_extract_glossary_workflow.py`

**Interfaces:**
- Produces: `NamePolicyResult(word_count, core_word_count, char_count, warnings)`。
- Produces: `assess_name_translation(term_type, translation, language) -> NamePolicyResult`。
- Produces: `find_name_collisions(rows, curated_rules=None) -> dict[str, list[str]]`。
- Produces: `build_name_review_packet(rows, language) -> dict[str, object]`。
- CLI 新增: `--name-review-packet-output PATH` 和 `--target-language LANG`。

- [ ] **Step 1: 写名称预算和重名失败测试**

```python
from glossary_extraction.name_policy import (
    assess_name_translation,
    build_name_review_packet,
    find_name_collisions,
)


def test_english_skill_name_budget_is_warning_only():
    result = assess_name_translation(
        term_type="ui_skill_name",
        translation="Megalodon Water Shield",
        language="EN",
    )

    assert result.word_count == 3
    assert result.char_count == 22
    assert "english_skill_word_budget" in result.warnings


def test_english_location_ignores_articles_and_prepositions_for_core_words():
    result = assess_name_translation(
        term_type="location_name",
        translation="Gates of Dawn",
        language="EN",
    )

    assert result.word_count == 3
    assert result.core_word_count == 2
    assert "english_location_core_word_budget" not in result.warnings


def test_different_cn_names_with_same_en_are_collisions():
    collisions = find_name_collisions(
        [
            {"CN": "鲨潮护盾", "EN": "Sharkguard", "TermType": "ui_skill_name"},
            {"CN": "鲨卫", "EN": "Sharkguard", "TermType": "ui_skill_name"},
        ],
        curated_rules=None,
    )

    assert collisions == {"sharkguard": ["鲨卫", "鲨潮护盾"]}


def test_collision_scope_includes_curated_project_names():
    collisions = find_name_collisions(
        [{"CN": "鲨潮护盾", "EN": "Sharkguard", "TermType": "ui_skill_name"}],
        curated_rules={
            "version": 1,
            "terms": {
                "鲨卫": {
                    "approved_en": "Sharkguard",
                    "term_type_override": "ui_skill_name",
                }
            },
        },
    )

    assert collisions == {"sharkguard": ["鲨卫", "鲨潮护盾"]}


def test_non_english_name_does_not_use_english_word_count_rule():
    result = assess_name_translation(
        term_type="ui_skill_name",
        translation="โล่คลื่นฉลาม",
        language="TH",
    )

    assert not any(warning.startswith("english_") for warning in result.warnings)
    assert "manual_semantic_unit_review" in result.warnings
```

- [ ] **Step 2: 运行名称策略测试并确认函数不存在**

Run:

```powershell
python -m pytest tests/test_name_policy.py -q
```

Expected: FAIL，缺少 `assess_name_translation`、`find_name_collisions`。

- [ ] **Step 3: 实现英语预算和非英语人工检查标记**

```python
@dataclass(frozen=True)
class NamePolicyResult:
    word_count: int
    core_word_count: int
    char_count: int
    warnings: tuple[str, ...]


ENGLISH_LOCATION_STOPWORDS = frozenset({"a", "an", "the", "of", "to", "in", "on", "at", "for"})


def plain_text(value: object) -> str:
    return " ".join(str(value or "").split())


def english_words(value: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*", plain_text(value))


def assess_name_translation(term_type: str, translation: str, language: str) -> NamePolicyResult:
    value = plain_text(translation)
    words = english_words(value) if language.upper() in {"EN", "ENG", "ENGLISH"} else []
    core_words = [word for word in words if word.lower() not in ENGLISH_LOCATION_STOPWORDS]
    warnings: list[str] = []

    if language.upper() in {"EN", "ENG", "ENGLISH"}:
        if term_type == "ui_skill_name" and len(words) > 2:
            warnings.append("english_skill_word_budget")
        if term_type == "ui_skill_name" and len(value) > 24:
            warnings.append("english_skill_char_budget")
        if term_type == "location_name" and len(core_words) > 2:
            warnings.append("english_location_core_word_budget")
        if term_type == "location_name" and len(value) > 28:
            warnings.append("english_location_char_budget")
    elif term_type in PROPER_NAME_TYPES:
        warnings.append("manual_semantic_unit_review")

    return NamePolicyResult(len(words), len(core_words), len(value), tuple(warnings))
```

预算警告不得改写译文。

- [ ] **Step 4: 实现项目内专名重名检查**

```python
def normalized_name(value: str) -> str:
    return re.sub(r"[\W_]+", "", str(value or "").strip().casefold(), flags=re.UNICODE)


def find_name_collisions(
    rows: list[dict[str, object]],
    curated_rules: dict[str, object] | None = None,
) -> dict[str, list[str]]:
    names: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if row.get("TermType") not in PROPER_NAME_TYPES:
            continue
        key = normalized_name(str(row.get("EN") or ""))
        cn = plain_text(row.get("CN"))
        if key and cn:
            names[key].add(cn)

    for cn, raw_state in (curated_rules or {}).get("terms", {}).items():
        state = raw_state if isinstance(raw_state, dict) else {}
        if state.get("term_type_override") not in PROPER_NAME_TYPES:
            continue
        key = normalized_name(str(state.get("approved_en") or ""))
        if key and str(cn).strip():
            names[key].add(str(cn).strip())

    return {
        key: sorted(cn_values)
        for key, cn_values in names.items()
        if len(cn_values) > 1
    }
```

同一 CN 的重复行不算名称碰撞；不同 CN 归一化后同名才算。

- [ ] **Step 5: 把名称检查结果写入候选审计字段**

构建候选行时先写入预算字段：

```python
"NameWordCount": policy.word_count,
"NameCoreWordCount": policy.core_word_count,
"NameCharCount": policy.char_count,
"NamePolicyWarnings": " | ".join(policy.warnings),
```

全部候选构建完成后，第二遍计算当前语言表候选与 curated 既有专名的项目级碰撞，再写入：

```python
collisions = find_name_collisions(rows_by_term, curated_rules)
for row in rows_by_term:
    collision_cn_values = collisions.get(normalized_name(row.get("EN", "")), [])
    has_collision = len(collision_cn_values) > 1
    row.update(
        {
            "NameCollision": "Yes" if has_collision else "No",
            "NameCollisionWith": " | ".join(collision_cn_values),
        }
    )
    if has_collision:
        row["Risk"] = "high"
```

名称碰撞行必须从正式交付排除，直到人工消除；长度超限只警告，不排除。

Task 3 的正式准入条件同步增加：

```python
and row["NameCollision"] != "Yes"
```

CLI 在写正式表前统计碰撞组；存在碰撞时仍写详细表和精简检查包，但不写正式表，并返回硬阻断：

```python
name_collision_count = len(
    {
        normalized_name(row.get("EN", ""))
        for row in all_rows
        if row.get("NameCollision") == "Yes"
    }
)
if name_collision_count:
    print(f"delivery_hard_blockers: {name_collision_count}")
    return 2
```

- [ ] **Step 6: 生成只含精简候选和少量证据的 AI 检查包**

```python
def build_name_review_packet(rows: list[dict[str, object]], language: str) -> dict[str, object]:
    candidates = []
    for row in rows:
        if row.get("TermType") not in PROPER_NAME_TYPES:
            continue
        candidates.append(
            {
                "ID": row.get("ID", ""),
                "CN": row.get("CN", ""),
                "translation": row.get("EN", ""),
                "term_type": row.get("TermType", ""),
                "category": row.get("Category", ""),
                "type_evidence": row.get("TypeEvidence", ""),
                "example_source": row.get("ExampleSource", ""),
                "example_translation": row.get("ExampleEN", ""),
                "word_count": row.get("NameWordCount", 0),
                "core_word_count": row.get("NameCoreWordCount", 0),
                "char_count": row.get("NameCharCount", 0),
                "warnings": row.get("NamePolicyWarnings", ""),
                "collision_with": row.get("NameCollisionWith", ""),
            }
        )
    return {
        "schema_version": 1,
        "task": "proper_name_review",
        "language": language,
        "instructions": [
            "Check category first; do not infer skill or location names from Chinese length.",
            "Check core meaning, naturalness, over-compression, and project-wide uniqueness.",
            "English skill names should normally fit 2 words and 24 characters.",
            "English location names should normally fit 2 core words and 28 characters.",
            "For non-English languages, judge about 2 core semantic units instead of English word count.",
            "Do not rewrite names merely to satisfy the budget when meaning or uniqueness would be lost.",
        ],
        "candidates": candidates,
    }
```

检查包不得包含完整语言表，只包含专名候选、相邻例句和告警。

- [ ] **Step 7: 接入 CLI 和详细工作簿**

新增参数：

```python
parser.add_argument(
    "--target-language",
    default="EN",
    help="Target language code used for proper-name QA. Default: EN",
)
parser.add_argument(
    "--name-review-packet-output",
    help="Optional compact JSON packet for AI review of skill and location names.",
)
```

当指定 `--name-review-packet-output` 时，使用现有 `write_json_output` 写出包；未指定时不产生过程文件。

详细工作簿表头加入 Task 3 至 Task 5 的审计字段，并增加只含专名的 `NameReview` 工作表。正式交付不得增加这些列。

- [ ] **Step 8: 运行名称 QA 单元测试和 CLI 集成测试**

Run:

```powershell
python -m pytest tests/test_name_policy.py tests/test_extract_glossary_workflow.py -q
```

Expected: PASS；检查包只包含专名候选，不包含普通术语和完整语言包行。

- [ ] **Step 9: 提交本任务**

```powershell
git add glossary_extraction/name_policy.py glossary_extraction/heuristics.py glossary_extraction/cli.py glossary_extraction/excel_io.py tests/test_name_policy.py tests/test_extract_glossary_workflow.py
git commit -m "feat: add proper-name QA and review packet"
```

---

### Task 6: 修正正式交付结构并增加读回门禁

**Files:**
- Create: `glossary_extraction/quality.py`
- Modify: `glossary_extraction/excel_io.py:732-762`
- Modify: `glossary_extraction/cli.py:169-181`
- Modify: `glossary_extraction/cli.py:704-715`
- Test: `tests/test_delivery_quality.py`
- Test: `tests/test_extract_glossary_workflow.py`

**Interfaces:**
- Produces: `write_final_workbook(output_path, final_rows, target_header, include_en2=False)`。
- Produces: `readback_delivery_workbook(path, target_header, require_target=True, include_en2=False) -> DeliveryQualityReport`。
- CLI 新增: `--include-en2`，默认关闭。
- 默认正式表: 单个 `Glossary` 工作表，表头为 `ID / CN / EN / 分类`。

- [ ] **Step 1: 写正式表结构和读回失败测试**

```python
def test_clean_delivery_keeps_one_target_and_category(tmp_path):
    output = tmp_path / "final.xlsx"
    rows = [
        {
            "ID": "SkillName_1001",
            "CN": "鲨潮护盾",
            "EN": "Sharkguard",
            "EN2": "Shark Shield",
            "Category": "技能名",
        }
    ]

    write_final_workbook(
        output_path=output,
        final_rows=rows,
        target_header="EN",
        include_en2=False,
    )

    workbook = load_workbook(output, read_only=True, data_only=True)
    assert workbook.sheetnames == ["Glossary"]
    sheet_rows = list(workbook["Glossary"].iter_rows(values_only=True))
    assert sheet_rows[0] == ("ID", "CN", "EN", "分类")
    assert sheet_rows[1] == ("SkillName_1001", "鲨潮护盾", "Sharkguard", "技能名")
    workbook.close()


def test_readback_blocks_duplicate_cn_and_name_collision(tmp_path):
    output = tmp_path / "invalid.xlsx"
    rows = [
        {"ID": "1", "CN": "鲨潮护盾", "EN": "Sharkguard", "Category": "技能名"},
        {"ID": "2", "CN": "鲨卫", "EN": "Sharkguard", "Category": "技能名"},
        {"ID": "3", "CN": "鲨卫", "EN": "Shark Ward", "Category": "技能名"},
    ]
    write_final_workbook(output, rows, "EN")

    report = readback_delivery_workbook(output, target_header="EN", require_target=True)

    assert report.duplicate_cn == 1
    assert report.name_collisions == 1
    assert report.hard_blockers == 2
```

- [ ] **Step 2: 运行测试并确认旧正式表仍包含 EN2、Buckets、Notes**

Run:

```powershell
python -m pytest tests/test_delivery_quality.py -q
```

Expected: FAIL。

- [ ] **Step 3: 把正式表改为单表干净交付**

```python
def write_final_workbook(
    output_path: Path,
    final_rows: list[dict[str, object]],
    target_header: str = "EN",
    include_en2: bool = False,
) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Glossary"
    headers = ["ID", "CN", target_header]
    if include_en2:
        headers.append("EN2")
    headers.append("分类")
    worksheet.append(headers)

    for row in final_rows:
        values = [row.get("ID", ""), row.get("CN", ""), row.get("EN", "")]
        if include_en2:
            values.append(row.get("EN2", ""))
        values.append(row.get("Category", ""))
        worksheet.append(values)

    style_sheet(worksheet)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(output_path)
    workbook.close()
```

- [ ] **Step 4: 实现结构化读回报告**

```python
@dataclass(frozen=True)
class DeliveryQualityReport:
    row_count: int
    blank_cn: int
    blank_target: int
    duplicate_cn: int
    blank_category: int
    invalid_category: int
    name_collisions: int
    hard_blockers: int


VALID_DELIVERY_CATEGORIES = frozenset(
    {
        "活动",
        "UI",
        "动作",
        "装备",
        "道具",
        "资源",
        "品质",
        "属性",
        "技能",
        "技能名",
        "地名",
        "纹章",
        "副本",
        "联盟",
        "英雄",
        "怪物",
        "宠物",
        "世界观",
        "邮件",
    }
)
```

`readback_delivery_workbook` 必须重新打开成品，检查：

- 工作表只能是 `Glossary`。
- 表头必须与 `include_en2` 配置一致。
- 空 CN、要求译文时的空目标语言、重复 CN、空分类、非法分类。
- 不同 CN 的技能名或地名出现相同归一化主译。
- `hard_blockers` 为以上硬问题数量之和；名称长度超限不计入 hard blocker。

- [ ] **Step 5: CLI 增加 EN2 显式开关并在写后读回**

```python
parser.add_argument(
    "--include-en2",
    action="store_true",
    help="Include EN2 in the clean delivery workbook. Disabled by default.",
)
```

写出后立即读回：

```python
write_final_workbook(
    output_path=final_output_path,
    final_rows=final_rows,
    target_header=canonical_output_header(args.target_column, "EN"),
    include_en2=args.include_en2,
)
quality_report = readback_delivery_workbook(
    final_output_path,
    target_header=canonical_output_header(args.target_column, "EN"),
    require_target=not args.source_only,
    include_en2=args.include_en2,
)
if quality_report.hard_blockers:
    print(f"delivery_hard_blockers: {quality_report.hard_blockers}")
    return 2
```

source-only 模式允许目标语言空值，但仍要求 CN 和分类非空。

- [ ] **Step 6: 运行交付结构和 CLI 回归**

Run:

```powershell
python -m pytest tests/test_delivery_quality.py tests/test_extract_glossary_workflow.py -q
```

Expected: PASS；默认正式表没有 EN2、Buckets、Notes，使用 `--include-en2` 时才保留 EN2。

- [ ] **Step 7: 提交本任务**

```powershell
git add glossary_extraction/quality.py glossary_extraction/excel_io.py glossary_extraction/cli.py tests/test_delivery_quality.py tests/test_extract_glossary_workflow.py
git commit -m "fix: enforce clean glossary delivery"
```

---

### Task 7: 更新工作流文档与完整回归

**Files:**
- Modify: `docs/workflow.md`
- Modify: `docs/terminology-thread-handoff.md`
- Modify: `scripts/run_glossary_harness.py`
- Modify: `tests/test_extract_glossary_workflow.py`
- Test: all repository tests and fixtures

**Interfaces:**
- Documents: 新的输入判断、专名通道、译文权威、名称检查、正式交付和人工复核边界。
- Harness: 新增三个 fixture 后仍兼容所有旧 fixture。

- [ ] **Step 1: 更新文档中的固定工作流**

文档必须明确写出：

```text
1. 扫描真实文件，识别中文主源、当前目标语言列、显式类型列和已有术语表。
2. 普通术语与专名分路处理。
3. 技能名、地名必须来自类型列、表/字段/ID 上下文或人工覆盖；不得按中文长度猜测。
4. 明确专名不受 min-hit 和 glossary-hit-threshold 限制。
5. 当前语言表非空译文优先；curated 只补空，observation 只作证据。
6. 英语技能名采用 2 词/24 字符软预算；英语地名采用 2 核心词/28 字符软预算。
7. 非英语名称按约 2 个核心语义单位人工检查，不套英语词数。
8. 项目内名称碰撞、分类冲突进入硬阻断；长度超限进入警告。
9. Codex 只读取专名精简检查包和少量句内证据，不读取完整语言包。
10. 正式表默认只保留 ID/CN/目标语言主译/分类，交付后重新打开校验。
```

分类列表增加 `技能名` 和 `地名`；保留原有 `技能`，用于技能机制、技能属性等非名称术语。

- [ ] **Step 2: 扫描计划要求是否全部有测试覆盖**

检查对应关系：

- 显式类型读取 → `test_records_from_rows_preserves_term_type_context`
- 不按四字长度猜测 → `test_four_character_text_is_not_a_skill_without_context`
- 单次专名保留 → `test_singleton_proper_names_bypass_frequency_threshold`
- 当前译文优先 → `test_current_language_table_translation_wins_over_curated`
- curated 只补空 → `test_curated_translation_only_fills_blank_current_translation`
- 技能名和地名预算 → `tests/test_name_policy.py`
- 名称碰撞 → `tests/test_name_policy.py` 与 `tests/test_delivery_quality.py`
- 干净交付 → `test_clean_delivery_keeps_one_target_and_category`
- source-only 兼容 → 现有 `test_cli_can_generate_source_only_final_terms`
- 公告句式模板不退化 → `tests/test_sentence_templates.py`

- [ ] **Step 3: 运行完整 pytest**

Run:

```powershell
python -m pytest -q
```

Expected: 全部 PASS，0 failed。

- [ ] **Step 4: 运行全部旧 fixture 和三个新增 fixture**

Run:

```powershell
python scripts/run_glossary_harness.py fixtures/core_regression.json fixtures/observation_feedback_regression.json fixtures/announcement_lookup_regression.json fixtures/announcement_ai_supplement_regression.json fixtures/announcement_sentence_templates_regression.json fixtures/proper_name_extraction_regression.json fixtures/current_translation_authority_regression.json
```

Expected: `all_passed: true`；每个报告 `pass: true`。

- [ ] **Step 5: 增加并运行真实结构 CLI 冒烟测试**

在 `CliIntegrationTests` 增加：

```python
def test_cli_proper_name_end_to_end_blocks_collision_then_passes(self):
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        input_path = root / "proper_names.xlsx"
        detail_path = root / "detail.xlsx"
        final_path = root / "final.xlsx"
        packet_path = root / "name_review.json"
        curated_path = root / "curated.json"
        observations_path = root / "observations.json"

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "名称"
        worksheet.append(["ID", "cn", "en", "术语类型"])
        worksheet.append(["SkillName_1001", "鲨潮护盾", "Sharkguard", "技能名"])
        worksheet.append(["SkillDesc_1001", "召唤鲨潮并获得护盾", "Summons a shark tide and gains a shield.", ""])
        worksheet.append(["SkillName_1002", "鲨卫", "Sharkguard", "技能名"])
        worksheet.append(["MapName_2001", "暮色海岸", "Dusk Coast", "地名"])
        worksheet.append(["Text_1", "终极挑战", "Final Challenge", ""])
        workbook.save(input_path)
        workbook.close()

        curated_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "terms": {
                        "鲨潮护盾": {
                            "approved_en": "Megalodon Water Shield",
                            "approved_en2": "",
                            "block_en2": True,
                            "ignore": False,
                            "note": "",
                            "category_override": "",
                            "term_type_override": "ui_skill_name",
                        }
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        args = [
            sys.executable,
            str(SCRIPT_PATH),
            str(input_path),
            "--output",
            str(detail_path),
            "--final-output",
            str(final_path),
            "--curated-rules",
            str(curated_path),
            "--observations-store",
            str(observations_path),
            "--min-hit",
            "5",
            "--glossary-hit-threshold",
            "10",
            "--target-language",
            "EN",
            "--name-review-packet-output",
            str(packet_path),
            "--no-project-brief",
        ]

        blocked = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(blocked.returncode, 2, msg=blocked.stderr or blocked.stdout)
        self.assertIn("delivery_hard_blockers: 1", blocked.stdout)

        workbook = load_workbook(input_path)
        workbook["名称"]["C4"] = "Shark Ward"
        workbook.save(input_path)
        workbook.close()

        passed = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(passed.returncode, 0, msg=passed.stderr or passed.stdout)

        final_workbook = load_workbook(final_path, read_only=True, data_only=True)
        self.assertEqual(final_workbook.sheetnames, ["Glossary"])
        rows = list(final_workbook["Glossary"].iter_rows(values_only=True))
        self.assertEqual(rows[0], ("ID", "CN", "EN", "分类"))
        lookup = {row[1]: row for row in rows[1:]}
        self.assertEqual(lookup["鲨潮护盾"][2], "Sharkguard")
        self.assertEqual(lookup["鲨潮护盾"][3], "技能名")
        self.assertEqual(lookup["暮色海岸"][3], "地名")
        self.assertNotIn("终极挑战", lookup)
        final_workbook.close()

        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        self.assertEqual({item["CN"] for item in packet["candidates"]}, {"鲨潮护盾", "鲨卫", "暮色海岸"})
        self.assertNotIn("召唤鲨潮并获得护盾", packet_path.read_text(encoding="utf-8"))
```

Run:

```powershell
python -m pytest tests/test_extract_glossary_workflow.py::CliIntegrationTests::test_cli_proper_name_end_to_end_blocks_collision_then_passes -q
```

Expected:

- 技能名和地名进入候选。
- 普通四字文本不因长度被判为技能名。
- 当前英语胜出并记录历史冲突。
- 名称碰撞导致退出码 2，消除碰撞后退出码 0。
- 正式表只有 `Glossary`，且表头为 `ID / CN / EN / 分类`。
- 检查包不包含完整语言包。

- [ ] **Step 6: 运行中文输出质量门禁**

Run:

```powershell
python D:\codex\codex\tools\output_quality_gate.py docs\workflow.md docs\terminology-thread-handoff.md docs\superpowers\plans\2026-07-24-proper-name-extraction-workflow-fix.md --expect-cjk
```

Expected: PASS，无 `????`、U+FFFD、null byte 或 mojibake。

- [ ] **Step 7: 核对仓库边界和未提交用户文件**

Run:

```powershell
git status --short --branch
git diff -- data/experience/observed_terms.json
git diff --name-only
```

Expected:

- `data/experience/observed_terms.json` 仍保持实施前的用户改动，未被本计划代码修改或暂存。
- 改动文件全部位于 `D:\codex\glossary-extraction-workflow`。
- 没有 `localization-workflow-studio` 文件。

- [ ] **Step 8: 提交文档和回归样例**

```powershell
git add docs/workflow.md docs/terminology-thread-handoff.md scripts/run_glossary_harness.py tests/test_extract_glossary_workflow.py fixtures/proper_name_extraction_regression.json fixtures/current_translation_authority_regression.json
git commit -m "docs: define proper-name extraction workflow"
```

不执行 `git push`；只有用户明确要求后，才在完整验证通过并确认暂存范围后推送。

---

## Final Acceptance

实施完成必须同时满足：

- 单次出现的明确技能名、地名可以进入正式术语候选。
- 普通四字文本不会仅因长度被判为技能名或地名。
- 类型证据冲突的候选进入人工复核，不进入正式交付。
- 当前语言表非空译文不会被 curated 或 observation 静默覆盖。
- 英语技能名、地名预算产生警告但不触发机械截断。
- 不同 CN 的专名主译碰撞会阻断交付。
- 非英语名称不执行英语词数硬判定。
- 正式表默认只有 `ID / CN / 目标语言主译 / 分类`。
- source-only、公告 lookup、官方句式模板、项目 brief 和原有 fixture 不退化。
- 完整 pytest、全部 harness、真实结构冒烟、中文输出门禁全部通过。
- `data/experience/observed_terms.json` 的现有用户改动未被覆盖或暂存。
