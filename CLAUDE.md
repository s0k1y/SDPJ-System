# 重要上下文

- 对话语言：中文（所有交互、解释、注释均使用中文）
- 本实例运行在 Trae IDE 的终端中，是 Claude Code CLI，不是 AGENTS.md 中定义的 SOLO Coder 智能体。AGENTS.md 是Trae IDE 中 SOLO Coder 专用的，不要混淆两者。
- 尽管不是 SOLO Coder，仍需遵守以下规范要求：

# 规范要求

- 当前工作常用到 OpenSpec 规范基础上，当用户特别明确要求你遵循 Specification Driven Development 规范中的 OpenSpec 规范时，必须在开展任何工作前必须先阅读完这些路径下的文件：`SDPJ-System/.trae/rules/`、`SDPJ-System/.trae/specs/`、`SDPJ-System/openspec/specs/`,此时你所做的一切行为均需遵循 OpenSpec 工作流（spec-driven），包括但不限于：规划任务、任务拆分、规范变更、代码实现、bug 修复等。所有变更必须基于规格文档进行，强制执行规范合规性检查，实施前必须验证所有规格文档，验证时必须基于规格文档进行测试，归档前必须确保规格与实现一致。规格文档是所有任务的唯一依据,但如果用户没有明确要求你遵循OpenSpec规范(未提及),此时你无需遵守。
- 如果不确定某个信息，请直接说"我不会"或"我不知道"，不要猜测或编造答案，幻觉和虚假信息是不可接受的。

---

# Karpathy 编码行为准则

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.
Tradeoff: These guidelines bias toward caution over speed. For trivial tasks, use judgment.

1. Think Before Coding
Don't assume. Don't hide confusion. Surface tradeoffs.
Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

2. Simplicity First
Minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

3. Surgical Changes
Touch only what you must. Clean up only your own mess.
When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

4. Goal-Driven Execution
Define success criteria. Loop until verified.
Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

These guidelines are working if: fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
