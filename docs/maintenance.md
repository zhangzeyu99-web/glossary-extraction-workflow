# 维护规范

## 维护目标

保证这套术语提取工作流长期可复用，输出口径稳定，避免随着项目推进逐渐失控。

## 维护频率

### 每次新版本语言表进入时

- 跑一次提取脚本
- 对新增的高风险词做人工复核
- 检查 `EN2` 是否出现新的稳定适配用法

### 每月一次

- 回归核心术语列表
- 看是否有新的系统词、货币词、按钮词进入常驻池
- 清理不再需要保留的 `EN2`

### 每季度一次

- 回顾风险词规则
- 更新样例数据
- 跑全量测试
- 检查 issue 模板和维护清单是否还适用

## 回归检查清单

重点检查：

- `报名 / Registration / Sign Up`
- `升级 / Level Up / Upgrade`
- `突破 / Evolve / Promote`
- `传说 / Legend / Legendary`
- `普通 / Ordinary / Normal`

如果这些高风险对照在新一轮提取里出现漂移，优先处理。

## 数据管理要求

- 不把客户原始语言表直接提交到仓库
- 仓库内只放脱敏样例
- 输出文件默认写到输入文件同目录，不作为仓库产物提交

## 提交规范

建议按以下粒度提交：

- `docs: update glossary workflow`
- `feat: improve glossary extraction heuristics`
- `test: add regression coverage for EN2 selection`
- `chore: refresh templates and maintenance checklist`

## 维护触发条件

以下情况发生时，建议立即维护：

- 新增大型活动系统
- 稀有度体系调整
- 翻译供应商切换
- LQA 反馈同一术语多种译法
- 新市场版本要求改写核心系统词

## 仓库内维护入口

- 常规维护：`docs/maintenance.md`
- 清单模板：`templates/maintenance_checklist.md`
- GitHub issue 模板：`.github/ISSUE_TEMPLATE/glossary-maintenance.md`
