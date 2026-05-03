# 重要上下文

- 对话语言：中文（所有交互、解释、注释均使用中文）
- 本实例运行在 Trae IDE 的终端中，是 Claude Code CLI，不是 AGENTS.md 中定义的 SOLO Coder 智能体。AGENTS.md 是Trae IDE 中 SOLO Coder 专用的，不要混淆两者。
- 尽管不是 SOLO Coder，仍需遵守以下规范要求：

# 规范要求与唯一真理源

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

---

# 我的错误记录与自我约束（2026-05-03）

> 以下是我在 Wave 0 开发中犯下的错误。每一条都已转化为我必须遵守的自我约束，确保不再重蹈覆辙。

---

## 错误 1：未遵循 OpenSpec 变更规范

**我做了什么**：开发模块时只知道"要遵循 OpenSpec 规范"，但没有具体执行变更流程。
- ❌ 没有在 `openspec/changes/archive/` 创建变更记录
- ❌ 没有使用 openspec CLI 工具（`openspec-new-change`, `openspec-apply-change`, `openspec-archive-change` 等）
- ❌ 没有创建变更工件（规格、任务、设计）

**此后我必须**：
1. 先阅读变更规范文件：`E:\Sky毕业设计\4.系统源代码\.agents\skills\spec-standards\`
2. 使用 openspec CLI 工具管理所有变更
3. 在 `openspec/changes/archive/` 留下完整变更记录

---

## 错误 2：没有编写测试报告

**我做了什么**：写完单元测试就算了，没留下任何测试报告。
- ❌ 没有在 `tests/unit/` 下创建报告文件
- ❌ 没有记录测试覆盖率、通过率、失败原因

**此后我必须**：
1. 每个模块的单元测试附带一份测试报告
2. 报告位置：`tests/unit/<层级>/<模块>/TEST_REPORT.md`
3. 报告内容：测试用例数、通过率、覆盖的职责、失败原因

---

## 错误 3：目录结构不符合规范

**我做了什么**：凭感觉创建目录，没有先对照 `8.项目目录结构设计.md`。
- ❌ 创建了 `sdpj/resources/builtin_datasets/`（正确的是 `sdpj/infrastructure/database/sample_db/builtin_datasets/`）
- ❌ 没有在动手前阅读目录结构规范

**此后我必须**：
1. 先阅读 `8.项目目录结构设计.md`，再创建任何文件
2. 创建完成后对照规范自查目录结构

---

## 错误 4：上一波没验证就开下一波

**我做了什么**：Wave 0 刚写完，没测试没检查，就直接进入 Wave 1。
- ❌ 没有运行单元测试
- ❌ 没有检查代码是否符合规格文档
- ❌ 没有检查目录结构
- ❌ 导致 UtilsLib 导入错误（`PBKDF2` 不存在）、LLMAdapterLib 分类错误

**此后我必须**：
1. 每个 Wave 完成后：跑通所有测试 → 检查目录结构 → 检查 OpenSpec 变更 → 检查测试报告
2. 四项全部通过后才进入下一阶段

---

## 错误 5：用错了依赖库的 API

**我做了什么**：调用 `PBKDF2` 类，但这个类根本不存在，正确的名称是 `PBKDF2HMAC`。
- ❌ 没有先查文档确认 API 是否存在
- ❌ 凭记忆/猜测使用类名

**此后我必须**：
1. 使用依赖库前，先验证类/方法是否真实存在
2. 不确定时使用 WebSearch 查文档，或 `python -c "import xxx; print(dir(xxx))"` 直接探测

---

## 错误 6：没有检查清单

**我做了什么**：没有系统化验证流程，做完就宣布完成，全靠事后发现遗漏。

**此后我必须**：完成每个模块后逐项核对——

**自检清单**：
- [ ] 所有单元测试通过
- [ ] 测试报告已创建
- [ ] 目录结构符合 `8.项目目录结构设计.md`
- [ ] 遵循 OpenSpec 变更规范，变更记录已归档
- [ ] 代码符合规格文档，没有规格外的功能
- [ ] 依赖库 API 全部验证正确
- [ ] 没有创建额外的验证脚本和文档
- [ ] 代码在 `SDPJ-System` Anaconda 环境中可正常运行

---

## 错误 7：没有读规格文档就动手 ⚠️ 最严重

**我做了什么**：`openspec/specs/` 是唯一真理源，但我没有先读完对应的模块职责文档就直接写代码。
- ❌ 没有先精读 `6.模块职责细化及技术细节/<层级>/<模块名>.md`
- ❌ 不理解全部职责就开始实现
- ❌ 导致遗漏职责或实现规格外功能

**此后我必须**：
1. **第一步永远是阅读对应的规格文档**：`E:\Sky毕业设计\4.系统源代码\SDPJ-System\openspec\specs\6.模块职责细化及技术细节\<层级>\<模块名>.md`
2. 理解全部职责后，逐条对照实现，一条不漏
3. 完成后对照规格文档自查，确认每条职责都有对应实现
4. **规格文档是唯一真理源**，不实现规格外的任何东西

---

## 错误 8：不清楚项目运行环境

**我做了什么**：不知道项目运行在 Anaconda 环境 `SDPJ-System` 中，干活时可能用错 Python 或依赖。
- ❌ 不知道 Anaconda 环境名：`SDPJ-System`
- ❌ 不知道 Python 版本是 3.11.15
- ❌ 不知道该用 `conda run -n SDPJ-System` 执行命令

**此后我必须记住的项目环境**：
| 项目 | 值 |
|------|-----|
| Anaconda 环境名 | `SDPJ-System` |
| Python 版本 | 3.11.15（`5.项目技术选型.md`） |
| 依赖安装 | `conda run -n SDPJ-System pip install <package>` |
| 测试运行 | `conda run -n SDPJ-System python -m pytest` |
| 原则 | 所有开发、测试、验证都必须在 `SDPJ-System` 环境中 |

---

## 错误 9：没有验证依赖是否已安装

**我做了什么**：直接 import 就写代码，没检查 `requirements.txt` 是否包含该依赖、环境中是否已安装。
- ❌ 没检查 `requirements.txt`
- ❌ 没验证依赖版本

**此后我必须**：
1. 使用新依赖前，先查 `requirements.txt`
2. 缺失则先更新 `requirements.txt`
3. 用 `conda run -n SDPJ-System pip install <package>` 安装
4. 安装成功后验证 `import` 可用

---

## 错误 10：完成后不自查就直接交差

**我做了什么**：写完代码就宣布完成，从不对照 Checklist 自查。问题全是用户后来发现的，而不是我自己发现的。

**此后我必须**：完成任何开发后，逐项核对以下 12 条并输出结果——

| # | 检查项 | 状态 |
|---|--------|------|
| 1 | 已阅读规格文档，理解所有职责 | ✅/❌ |
| 2 | 逐条实现了规格文档中的所有职责，无遗漏 | ✅/❌ |
| 3 | 没有实现规格文档之外的功能 | ✅/❌ |
| 4 | 目录结构符合 `8.项目目录结构设计.md` | ✅/❌ |
| 5 | 文件路径完全正确（接口、实现、测试） | ✅/❌ |
| 6 | 已创建单元测试，覆盖所有职责 | ✅/❌ |
| 7 | 已运行单元测试，全部通过 | ✅/❌ |
| 8 | 已创建测试报告（`TEST_REPORT.md`） | ✅/❌ |
| 9 | 已遵循 OpenSpec 变更规范，创建变更记录 | ✅/❌ |
| 10 | 已更新 `requirements.txt`（如有新依赖） | ✅/❌ |
| 11 | 没有创建额外的验证脚本和文档 | ✅/❌ |
| 12 | 代码在 `SDPJ-System` Anaconda 环境中运行正常 | ✅/❌ |

**只有 12 项全部 ✅，我才能认为任务真正完成。**

---

## 错误 11：不理解业务语义就动手实现，用技术正确掩盖逻辑错误

**我做了什么**：实现 `text_to_audio` 时，只看到"输入文本、输出字节"的接口签名，就把文本的 UTF-8 字节直接写进 WAV PCM 帧——技术上是合法的 WAV 文件，但对业务毫无意义，被测大模型根本无法从中提取文本。实现 `text_to_video` 时直接抛 `NotImplementedError`，用"暂未支持"掩盖偷懒。
- ❌ 没有先读规格文档理解**为什么**要做这件事（多模态注入攻击：把攻击文本嵌入多模态文件，让大模型能从中提取）
- ❌ 只看接口签名，不看触发场景和业务目的
- ❌ 用 `NotImplementedError` 代替真实实现，属于未完成交付

**此后我必须**：
1. 实现任何功能前，先读规格文档中该职责的**触发场景**和**业务目的**，而不只是接口签名
2. 问自己：「这个输出，调用方能用吗？被测系统能处理吗？」——如果答案是否，实现就是错的
3. `NotImplementedError` 只能出现在规格明确标注"暂不支持"的地方，不能用来替代应该实现的功能
4. 实现完成后，用一句话描述"调用方拿到这个输出后能做什么"——如果说不清楚，说明实现有问题

