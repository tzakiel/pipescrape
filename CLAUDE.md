# Claude Code Instructions

## Large Work Estimation Rule

Before starting any large automated work — modifying many files, long loops, large cache writes, or any task estimated to take more than a few steps — you must:

1. Estimate the scope (how many entries, files, operations)
2. Describe the approach and expected time/effort
3. Ask the user explicitly if they want to proceed

Do not begin the work until confirmed. If a task grows larger than initially scoped mid-execution, pause and re-confirm.

## Git Push

NEVER run `git push` without explicit user confirmation. Always stop after committing and ask "Want me to push?" — no exceptions, even when it seems like a natural next step.

## Brand / Blend / Alias Changes

Before creating a new brand, creating a new blend, or adding any entry to brand or blend alias lists:

1. State exactly what you plan to add and why
2. Wait for explicit user confirmation before writing anything

No exceptions — this applies even when the addition seems obvious or low-risk.

## Batch Work

When processing large lists (e.g. blend_cache.json entries from unmatched.log):
- Work in batches of 50 entries at a time
- Report what was written after each batch
- Wait for "continue" before starting the next batch
