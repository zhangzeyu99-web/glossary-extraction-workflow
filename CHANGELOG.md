# Changelog

本文件记录术语提取工作流仓库的版本变化，方便后续维护 README、脚本能力和回归基线。

## v0.3.0 - 2026-07-07

### Added

- Documented the current repository version and supported workflow surface in `README.md`.
- Added this changelog and a plain `VERSION` file for lightweight repository version tracking.
- Marked the current workflow baseline as `v0.3.0`, covering:
  - full language-table glossary extraction,
  - source-only extraction,
  - project brief generation,
  - announcement-specific glossary lookup,
  - explicit multi-language announcement lookup,
  - optional AI supplement packet/file/OpenAI provider flow,
  - Codex-thread AI supplement review protocol,
  - regression harness coverage for core extraction, observation feedback, announcement lookup, and AI supplement behavior.

### Notes

- This release is a documentation and repository-management update. It does not change script behavior.

## v0.2.0 - 2026-06-09

### Added

- Added AI supplement support for announcement glossary lookup.
- Added compact AI packet generation and structured response merge behavior.
- Added Codex-thread supplement guidance so model-assisted leak checks do not require putting full language tables into model context.

## v0.1.0 - 2026-05-09

### Added

- Added the first announcement term lookup workflow.
- Established the initial glossary extraction harness baseline.
- Added delivery-ready glossary output conventions for `ID / CN / EN / EN2`.
