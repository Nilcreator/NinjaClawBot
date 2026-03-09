---
name: ninjaclawbot-implementation
description: Use for substantial NinjaClawBot implementation tasks that require research, repository/code review, phased planning, user approval before coding, mandatory linting/testing gates, Raspberry Pi validation planning, and documentation updates.
---

# NinjaClawBot Implementation Lifecycle

Follow this workflow in order. Do not skip steps.

## Step 1: Understand the request
Extract:
- requested outcome
- constraints
- target environment
- hardware interfaces involved
- safety risks
- files/modules likely involved

## Step 2: Research and inspect before planning
- If the task involves OpenAI/Codex/API behavior, use the OpenAI Docs MCP first.
- If the task involves third-party libraries, setup, package behavior, or current API usage, use Context7 first.
- If the task involves repository understanding or code review, use Serena first.
- If Serena is available, activate the project and prefer:
  - list_dir
  - find_file
  - get_symbols_overview
  - find_symbol
  - search_for_pattern
- Only use read_file for line-by-line review when symbolic review is insufficient or for non-code files.
- If repo/issue/PR context matters, use GitHub MCP.

## Step 3: Produce a phased plan
Create a detailed phase-by-phase implementation plan that includes:
- goal of each phase
- files/functions/drivers likely to change
- lint/test checks for the phase
- Raspberry Pi validation needed
- documentation files to update

Present the plan to the user and wait for approval before coding.

## Step 4: Implement phase-by-phase
- Make the smallest reasonable change for the current phase.
- Keep changes integrated with the existing codebase.
- Prefer modifying existing files over creating isolated new files.

## Step 5: Mandatory quality gate
Do not proceed to the next phase until the current phase passes quality checks.
Prefer repo-defined commands. Otherwise use:
- python -m compileall .
- ruff check .
- ruff format --check .
- pytest -q

If type checking is already used in the project, also run:
- mypy .

If any gate fails:
- stop
- fix the issue
- rerun checks
- only then continue

## Step 6: Raspberry Pi validation output
For hardware-relevant changes, generate:
- safe smoke tests
- communication tests
- actuator-moving tests
- expected results
- rollback notes

## Step 7: Documentation is mandatory
Before completion, review and update:
- README.md
- DevelopmentGuide.md
- DevelopmentLog.md

## Step 8: Final response
Summarize:
- changes made
- lint/test outcomes
- Pi validation required or completed
- docs updated
- remaining risk or next step