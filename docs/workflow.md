# 术语提炼工作流

## 目标

从完整翻译语言表中稳定提炼出：

- 高频重复词
- 易混淆近义词
- 需要全局统一的系统词
- 需要保留第二套适配译法的术语

最终形成可交付的 `ID / CN / EN / EN2` 术语表。

## 适用场景

- 游戏出海本地化
- 新版本语言表梳理
- 活动、付费、战斗系统术语统一
- 翻译供应商切换前的术语基线搭建

## 标准流程

### 1. 输入审计

先确认：

- 原文列是否稳定，默认是 `cn`
- 目标语言列是否稳定，默认是 `en`
- `ID` 是否可追溯
- 是否存在大量占位符、富文本标签、测试串、活动临时文案

### 2. 项目审查与风格提示词

扫描完整语言包时，同步生成项目审查文件，用于指导后续翻译风格：

- 根据词条内容推断题材方向，例如战斗/RPG、基地经营、活动商业化、社交公会、飞行射击、末日生存、剧情叙事
- 根据术语分布判断翻译重点，例如 UI 操作、战斗属性、资源货币、系统玩法、角色装备
- 根据已有英文覆盖率判断是否应优先尊重历史译文和手动适配
- 输出 `*_project_brief_YYYYMMDD.md`，包含项目快照、内容信号、术语分布、风格规则和可复制翻译提示词

常用命令：

```bash
python scripts/extract_glossary.py /path/to/language_table.xlsx \
  --project-name "Project Name" \
  --project-brief-output /path/to/project_brief.md \
  --translation-prompt-output /path/to/translation_prompt.txt
```

如果某次只跑术语、不需要项目审查，可加：

```bash
python scripts/extract_glossary.py /path/to/language_table.xlsx \
  --no-project-brief
```

项目审查是语言表推断结果，不替代正式项目设定；如果发行地区、人称、世界观或品牌语气已有明确规范，应以项目规范为准。

### 3. 原文提取

术语只从原文列抽取，不从译文反推。原因：

- 原文是术语主键
- 同一术语可能被译为不同英文
- 译文只能用于判断是否漂移，不适合拿来定义术语边界

### 4. 候选筛选

优先保留：

- 高频出现
- 多系统复用
- 玩家操作强相关
- 数值、资源、稀有度、玩法、按钮词

优先排除：

- 整句描述
- 一次性剧情文案
- 测试串
- 嵌入图片或复杂富文本的整段内容

### 5. 英文对齐

用英文列做两件事：

- 找示例英语 `EN`
- 检查实际译文是否出现另一套稳定用词 `EN2`

如果语言表还没有英文列，则先启用源文-only 模式，只提取 `CN` 候选并保留 `ID / CN / EN / EN2` 结构。后续拿到人工确认或翻译结果后，再用回灌脚本补齐规则层。

源文-only 项目建议按状态分阶段交付：

- `项目名-已提取-YYYYMMDD.xlsx`
- `项目名-预翻译-YYYYMMDD.xlsx`
- `项目名-已分类-YYYYMMDD.xlsx`
- `项目名-已审校-YYYYMMDD.xlsx`
- `项目名-已回灌-YYYYMMDD.xlsx`

分类整理版主表使用 `ID / CN / EN / EN2 / 分类`，并将 `分类` 放在最后一列。同类术语应连续排列，便于翻译、LQA 和术语管理员筛选。完整复盘见 [source-only delivery retrospective](source-only-delivery-retrospective.md)。

### 6. 示例与手动适配拆分

拆分原则：

- `示例`
  和标准英语一致，或只是基于标准英语的短语扩展
- `手动适配`
  在实际短句里出现了稳定、可复用、与标准英语不同的另一套用词

示例：

- `Registration` 和 `Registration Countdown`
  仍算示例同族，不拆出 `EN2`
- `Registration` 和 `Sign Up`
  是两套不同译法，应写入 `EN2`

### 6.1 规则层与观察层反哺

如果某个术语已经被人工确认：

- 优先使用 `approved_en`
- 优先使用 `approved_en2`
- 如果 `block_en2 = true`，则不再自动派生 `EN2`

如果某个术语在历史跑表里已经多次出现：

- 合并 `observed_exact_candidates`
- 合并 `observed_example_usages`
- 合并 `observed_manual_adaptations`

这样可以把一次人工判断沉淀为规则层，把后续运行的真实观察沉淀为自动学习层。

### 7. 风险判定

以下情况优先列为高风险：

- 同一原文对应多个英文版本
- 稀有度、资源、数值、按钮操作词
- 高命中但大多以内嵌形式出现
- 实际短句里存在手动适配

### 8. 最终交付

最终表只保留：

- `ID`
- `CN`
- `EN`
- `EN2`

其中：

- `EN` 是标准示例译法
- `EN2` 只在替代译法稳定成立时填写，否则留空

## 自动回归

每次优化提取逻辑后，应使用 harness 跑 fixture：

```bash
python scripts/run_glossary_harness.py \
  fixtures/core_regression.json \
  fixtures/observation_feedback_regression.json
```

通过后再跑真实语言表。

## 人工确认回灌

人工确认完 `ID / CN / EN / EN2` 交付表后，应尽快回灌到规则层：

```bash
python scripts/import_curated_glossary.py /path/to/final_glossary.xlsx \
  --curated-rules data/experience/curated_terms.json
```

这样下一次跑表时，标准 EN、稳定 EN2 和明确禁止 EN2 的术语都会直接继承。

## 推荐复核顺序

1. 稀有度
2. 数值属性
3. 操作按钮
4. 活动和付费系统
5. 非空 `EN2`

## 版本维护建议

- 每次大版本或新活动上线前重跑一遍
- 每月回顾一次 `EN2` 是否仍有保留价值
- 将争议项单独列入 review 列表，不直接写死进术语库
