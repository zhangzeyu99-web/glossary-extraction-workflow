# Glossary Extraction Workflow

> Game localization glossary extraction workflow for Excel language tables, bilingual term review, and delivery-ready `ID / CN / EN / EN2` exports.

这是一个面向**游戏出海本地化团队**的术语提取仓库，用于从完整语言表中提取高频、易混淆、需要统一维护的术语，并生成交付版 `ID / CN / EN / EN2` 术语表。

**Keywords:** glossary extraction, game localization glossary, terminology workflow, Excel language table, translation glossary, EN EN2 mapping, localization term management, game translation operations.

## Why This Project Exists

Localization teams often store useful term decisions inside huge language tables, chat threads, or ad hoc spreadsheets. This project turns that mess into a repeatable workflow that:

- extracts high-value terms from full language tables
- separates standard examples from manual adaptations
- preserves reusable review knowledge across versions
- produces delivery-ready glossary files for translators, LQA, and terminology owners

## 中文简介

面向游戏出海本地化团队的可复用仓库，用于从完整语言表中提取高频、易混淆、需要统一维护的术语，并生成交付版 `ID / CN / EN / EN2` 术语表。

## 仓库目标

- 把术语提取从“临时人工整理”变成“可重复执行的标准流程”
- 用统一规则区分 `示例用法` 和 `手动适配`
- 输出可直接下发给翻译、LQA、术语管理员的交付表
- 给后续版本迭代留下测试、模板、维护清单和回归基线

## 目录结构

```text
.
├─ .github/
│  ├─ ISSUE_TEMPLATE/
│  └─ workflows/
├─ docs/
├─ examples/
├─ scripts/
├─ templates/
├─ tests/
├─ .gitignore
└─ requirements.txt
```

## 快速开始

### 1. 安装依赖

```bash
python -m pip install -r requirements.txt
```

### 2. 准备语言表

最小表头要求见 [templates/language_table_minimum_headers.tsv](templates/language_table_minimum_headers.tsv)。

默认约定：

- `ID`：文本 ID
- `cn`：中文原文
- `en`：英语译文

### 3. 执行提取

```bash
python scripts/extract_glossary.py /path/to/language_table.xlsx
```

如果表头不是默认值，可以显式传参：

```bash
python scripts/extract_glossary.py /path/to/language_table.xlsx \
  --sheet Sheet0 \
  --id-column ID \
  --source-column cn \
  --target-column en
```

默认会同时读写两层经验数据：

```bash
python scripts/extract_glossary.py /path/to/language_table.xlsx \
  --curated-rules data/experience/curated_terms.json \
  --observations-store data/experience/observed_terms.json
```

### 4. 产物说明

脚本默认在输入文件同目录输出两份 Excel：

- `*_glossary_details_YYYYMMDD.xlsx`
  工作明细版，包含候选术语、风险、示例用法、手动适配、差异说明
- `*_ID_CN_EN_EN2_YYYYMMDD.xlsx`
  干净交付版，只保留 `ID / CN / EN / EN2`

同时会更新：

- `data/experience/curated_terms.json`
  人工确认层，保存 `approved_en / approved_en2 / block_en2 / note`
- `data/experience/observed_terms.json`
  自动观察层，保存历史出现过的候选、手动适配、命中次数和上次输入指纹

### 5. 回灌人工确认结果

当你已经拿到人工确认过的最终交付表，可以直接回灌到人工规则层：

```bash
python scripts/import_curated_glossary.py /path/to/final_glossary.xlsx \
  --curated-rules data/experience/curated_terms.json
```

默认读取 `Glossary` sheet，按 `ID / CN / EN / EN2` 回写规则：

- `EN` 写入 `approved_en`
- `EN2` 非空时写入 `approved_en2`
- `EN2` 为空时自动设置 `block_en2 = true`

## EN 与 EN2 的口径

- `EN`
  标准示例英语。优先使用独立词条或最短可成立示例中的译法。
- `EN2`
  手动适配英语。仅当实际短句里稳定出现另一套用词时才写入；噪音词、不稳定上下文不强行写入。

典型示例：

- `报名` -> `Registration / Sign Up`
- `传说` -> `Legend / Legendary`
- `升级` -> `Level Up / Upgrade`
- `突破` -> `Evolve / Promote`

## 工作流文档

- [docs/workflow.md](docs/workflow.md)：完整提炼流程
- [docs/maintenance.md](docs/maintenance.md)：维护与回归规范

## Harness 回归

仓库内置 fixture 驱动的 harness，用来做回归验证：

```bash
python scripts/run_glossary_harness.py fixtures/core_regression.json
```

可选输出 JSON 报告：

```bash
python scripts/run_glossary_harness.py fixtures/core_regression.json \
  --report-output output/harness-report.json
```

harness 会检查：

- 预期术语是否被提取
- `EN / EN2` 是否命中
- 不应进入术语表的词是否被误提
- 当前输出是否和历史基线漂移

## 自动积累经验

经验层现在拆成两部分：

- [data/experience/curated_terms.json](data/experience/curated_terms.json)
- [data/experience/observed_terms.json](data/experience/observed_terms.json)

人工确认层支持三类核心信息：

- `approved_en`
  已确认的标准 EN
- `approved_en2`
  已确认的手动适配 EN2
- `block_en2`
  明确禁止自动派生 EN2 的术语

自动观察层会在每次运行后累积：

- `observed_exact_candidates`
- `observed_example_usages`
- `observed_manual_adaptations`
- `seen_runs`
- `last_seen_at`

提取时会先读人工确认层，再把历史观察合并进候选判断，减少同一术语在不同版本里来回漂移。

## 模板与示例

- [templates/final_glossary_headers.tsv](templates/final_glossary_headers.tsv)
- [templates/language_table_minimum_headers.tsv](templates/language_table_minimum_headers.tsv)
- [templates/maintenance_checklist.md](templates/maintenance_checklist.md)
- [examples/README.md](examples/README.md)

## 测试

```bash
python -m pytest
```

额外建议每次大改后再跑一遍 harness：

```bash
python scripts/run_glossary_harness.py \
  fixtures/core_regression.json \
  fixtures/observation_feedback_regression.json
```

当前仓库默认提供本地测试命令；如后续账号具备 `workflow` 权限，可再补 GitHub Actions。

## 维护建议

- 每个版本新增语言表后跑一遍脚本
- 对 `EN2` 非空的术语做人工复核
- 每月做一次术语回归，检查新活动、新系统、新养成线是否引入新词
- 不把客户原始语言表直接提交到仓库，示例文件只保留脱敏样例
