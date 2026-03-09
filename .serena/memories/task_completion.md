# Task Completion Requirements
1. Understand the request fully, including constraints, safety concerns, hardware impact, target files, and expected outputs.
2. Research and review before planning. Prefer Serena for repo/code understanding, Context7 for third-party libraries, OpenAI docs MCP for OpenAI-related topics, and GitHub MCP for repository/PR context.
3. Produce a phased implementation plan and get user approval before coding.
4. Implement phase by phase with small, reviewable diffs.
5. After every implementation phase, run validation gates: `python -m compileall .`, `ruff check .`, `ruff format --check .`, `pytest -q`, and `mypy .` when applicable.
6. For hardware-facing work, produce a Raspberry Pi validation checklist covering smoke tests, device communication, actuator movement, and power-risk checks with rollback steps.
7. Update `README.md`, `DevelopmentGuide.md`, and `DevelopmentLog.md` before closing.
8. Final handoff must summarize changes, validations, remaining Pi checks, docs updated, user test instructions, and the recommended next step.