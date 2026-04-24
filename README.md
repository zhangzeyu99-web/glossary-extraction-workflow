# 术语提取工作流

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

### 4. 产物说明

脚本默认在输入文件同目录输出两份 Excel：

- `*_glossary_details_YYYYMMDD.xlsx`
  工作明细版，包含候选术语、风险、示例用法、手动适配、差异说明
- `*_ID_CN_EN_EN2_YYYYMMDD.xlsx`
  干净交付版，只保留 `ID / CN / EN / EN2`

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

## 模板与示例

- [templates/final_glossary_headers.tsv](templates/final_glossary_headers.tsv)
- [templates/language_table_minimum_headers.tsv](templates/language_table_minimum_headers.tsv)
- [templates/maintenance_checklist.md](templates/maintenance_checklist.md)
- [examples/README.md](examples/README.md)

## 测试

```bash
python -m pytest
```

当前仓库默认提供本地测试命令；如后续账号具备 `workflow` 权限，可再补 GitHub Actions。

## 维护建议

- 每个版本新增语言表后跑一遍脚本
- 对 `EN2` 非空的术语做人工复核
- 每月做一次术语回归，检查新活动、新系统、新养成线是否引入新词
- 不把客户原始语言表直接提交到仓库，示例文件只保留脱敏样例
