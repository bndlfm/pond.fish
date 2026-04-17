# Plan: SKILL.md (agentskills.io) Implementation

This plan outlines the steps to make `pond` a modular agent using the SKILL.md pattern for progressive disclosure of expertise and tools.

## Phase 1: Foundation
- [ ] Create `skills/` directory structure in `~/.config/fish-ai/`.
- [ ] Implement `SkillManager` class in `agent.py` to handle discovery and parsing.
- [ ] Update `SYSTEM_PROMPT` to include the dynamic Skill Catalog.

## Phase 2: Activation Logic
- [ ] Implement `activate_skill(name)` tool.
- [ ] Logic to append `SKILL.md` body to conversation turns upon activation.
- [ ] Ensure activated skills persist across turns in the session JSON.

## Phase 3: Scripted Tools
- [ ] Implement automatic discovery of executables in `skills/*/scripts/`.
- [ ] Use `--info` flag on scripts to generate OpenAI-compatible tool schemas.
- [ ] Map AI tool calls (e.g., `skill_name_script_name`) to subprocess executions.

## Phase 4: Audit & UI
- [ ] Add Magenta color-coding for skill signals.
- [ ] Implement truncated output for skill results (4-line limit).
- [ ] Create an example `weather` or `project-helper` skill to verify.

## Phase 5: Documentation
- [ ] Document the SKILL.md format in `README.md`.
- [ ] Provide a template for users to create their own skills.
