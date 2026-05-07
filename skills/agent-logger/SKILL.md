---
name: "agent-logger"
description: "Records agent logs with structured markdown files. Invoke when completing complex tasks, learning new knowledge, making serious errors, being corrected by user, when no logs in recent 8 conversations, when self-deemed necessary, or when user requests logging."
---

# Agent Logger

This skill creates structured log entries for the agent to track experiences, learnings, and reflections.

## When to Use

Invoke this skill in these scenarios:
- **After completing a complex task**: When finishing multi-step or non-trivial work
- **When learning new knowledge**: After discovering new technologies, patterns, or insights
- **After making serious errors**: When significant mistakes occur that should be documented for future reference
- **When being corrected by user**: When the user corrects your mistakes or provides corrections to your responses
- **When no logs in recent 8 conversations**: When the last 8 conversation turns have not resulted in any log entries
- **Self-reflection**: When you deem it necessary to record important information
- **User request**: When the user explicitly asks to log something

## Logging Process

### Step 0: Brainstorm Logging Angles (MANDATORY)

**Before writing any log, pause and brainstorm what angles exist for this task.** Complex tasks often warrant multiple logs from different perspectives. Skipping this step leads to missed insights.

#### Brainstorm Checklist

Go through these questions:

1. **Result angle** — What was accomplished? What changed? (→ type: `log`)
2. **Learning angle** — What did I learn? What surprised me? What would I do differently? (→ type: `learning`)
3. **Error angle** — What went wrong? How was it fixed? What prevented it from happening again? (→ type: `error`, use `error_pattern` to classify)
4. **Process angle** — Was the process efficient? What bottlenecks existed? How could the workflow improve? (→ type: `reflection`)
5. **Decision angle** — Were there non-obvious design decisions? Trade-offs that future readers should understand? (→ type: `log` or `reflection`)
6. **Collaboration angle** — Did interaction with other agents/tools/reviewers yield insights? (→ type: `learning`)

#### Decision Rules: Split or Combine?

| Situation | Action |
|-----------|--------|
| Only one angle has substance | Write 1 log, skip the rest |
| Two angles are closely related and each is thin | Combine into 1 log with clear sections |
| Each angle has substantial content (3+ paragraphs) | Split into separate logs, cross-link them |
| A "result" log exists but "learning" angle is rich | Create a separate learning log (e.g., a complex bug fix where the lesson deserves its own space) |

#### Present the Plan

For complex tasks (3+ angles with substance), present the brainstorm to the user:

```
这个任务可以从以下角度记录：
1. 结果总结 — 做了什么、改了什么
2. 经验教训 — 过程中学到的东西
3. 过程反思 — 流程哪里可以改进
```

### Step 1: Get Current Time
- Get current time in ISO 8601 format with timezone
- Format example: `2026-03-18T20:56:00+08:00`

### Step 2: Create Log Directory
- Check if `<workspace>/.log/<yyyy>/<MM>/<dd>/` exists
- If not, create the directory structure (year/month/day nested directories)
- `<workspace>` is the root directory of project workspace

### Step 3: Generate Log File
- Create markdown file in the date directory
- File naming format: `log-<topic>.md`
- Example: `log-completed-task.md`

## Log File Structure

### YAML Frontmatter
```yaml
---
title: "Topic Title" # Always use English for title
created: "2026-03-18T20:56:00+08:00"
type: "log"  # or "learning", "error", "reflection", etc.
author: "<当前AI模型> via <当前Agent平台>"  # AI Model via Agent Platform/Tool
tags: ["#tag1", "#tag2", "#tag3"] # Use graph-compatible tags
language: "zh"  # or "en", etc.
error_pattern: "<错误模式>"  # Optional, for type=error only. Classify the error pattern for cross-log retrieval. Examples: "信息虚构", "流程违规", "修改不完整", "工具盲区"
---
```

### Markdown Content
```markdown
# Topic Title

**Time**: 2026-03-18T20:56:00+08:00

**Tags**: #tag1 #tag2 #tag3

## Content

[Detailed log content here]
```

## Content Guidelines

### Language
- **YAML frontmatter title**: Always use English for consistency and cross-language linking
- **Markdown content**: Use the user's preferred language for all content
- **Markdown headings**: Use the user's preferred language (same as content)
- Match the language used in the conversation

### One Topic Per Document
- **Single focus**: Each log document should focus on only one topic or theme
- **Multiple topics**: If you need to record multiple topics, create separate log documents for each
- **Benefits**: This makes logs easier to search, reference, and connect in knowledge graphs
- **Examples**:
  - ✅ Good: One document for "Learning React Hooks", another for "Learning Redux"
  - ❌ Bad: One document mixing both React Hooks and Redux learnings
- **Related topics**: Use bidirectional links `[[Topic Name]]` to connect related documents

### Privacy and Security
- **Never log sensitive information**: Do not include passwords, cookies, tokens, API keys, authentication credentials, or any other sensitive data
- **Use placeholders**: Replace sensitive information with descriptive placeholders
- **Examples of sensitive data to avoid**:
  - Passwords: `password123` → `YOUR_PASSWORD`
  - API Keys: `sk-1234567890abcdef` → `YOUR_API_KEY`
  - Tokens: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` → `YOUR_TOKEN`
  - Cookies: `session_id=abc123` → `YOUR_COOKIE`
  - Database credentials: `user=admin&pass=secret` → `DB_CREDENTIALS`
- **Why this matters**: Logs may be shared, backed up, or accessed by others. Protecting sensitive information prevents security breaches
- **General principle**: If it's a secret, authentication credential, or personally identifiable information, use a placeholder

### Path Handling
- **Never log fragile file paths outside `.log` directory**: Do not include absolute paths, long relative paths, or `../` traversal paths in log content — these break when files are reorganized. Short conventional module names used as descriptive labels (e.g., `models/user.py`, `hooks/useState.ts`) are acceptable as identity references, not location instructions
- **Paths are ephemeral**: Files get moved, renamed, deleted, or reorganized constantly. Both `d:\project\src\utils.js` and `src/utils.js` become equally useless once the file changes location or no longer exists
- **Reference code by identity, not location**: When referring to code, use descriptive identifiers instead of paths:
  - Use **file name + entity name**: `helpers.js 中的 formatDate() 函数`, `UserModel class in models/user.py`
  - Use **inline code snippets**: Paste the relevant code directly into the log so it's self-contained
  - Use **descriptive labels**: `项目根目录的 package.json`, `agent-logger skill 的 SKILL.md`
- **Use bidirectional links `[[]]` for cross-references, never `[]()`**: The standard markdown link syntax `[](path/to/file)` requires a real filesystem path and breaks when the target moves. Use bidirectional wikilinks `[[Topic Name]]` instead — they are purely semantic identifiers with no path dependency
  - **Uniqueness is required**: The link target must be uniquely identifiable. Generic names like `[[SKILL]]` or `[[README]]` are ambiguous when multiple skills/repos exist
  - **⚠️ CRITICAL: Always use the SHORTEST name that is globally unique**. Do NOT default to long namespace-prefixed names. Follow this decision order:
    1. **Try filename only first** (shortest): `[[dream-entry-selector.py]]`, `[[prs]]`
    2. **If not unique, add parent directory**: `[[log-memory-searcher/SKILL]]`, `[[gh-cli/references/prs]]`
    3. **If still not unique, add more levels until unique**: `[[agent-logger/skills/log-memory-searcher/SKILL]]`
    4. **Validation rule**: Always verify with `fd` after writing. If `fd` returns exactly 1 match, the name is good. If 0 or 2+, adjust.
  - **Why shortest?** Long paths are fragile (break on file moves), harder to read, and signal false precision. A wikilink is a semantic identifier, not a filesystem address.
  - **Suffix rules**:
    - `.md` files: **No suffix needed** — `[[agent-logger/SKILL]]` links to `agent-logger/SKILL.md` (standard wikilink convention)
    - Non-md files: **Keep the suffix** — `[[ollama-tool-call-demo.ts]]`, `[[package.json]]` to distinguish file types
  - **Description required**: Every wikilink must be followed by a brief text description explaining the relationship or context. A bare `[[link]]` without explanation is insufficient — the reader cannot understand why the link is relevant without following it
    - ✅ Good: `[[dream-entry-selector.py]]：本次新增的入梦提示选择脚本`
    - ✅ Good: `[[agent-logger/SKILL]]：日志记录规范，定义了 wikilink 用法`
    - ❌ Bad: `[[dream-entry-selector.py]]` — no description, unclear why it's linked
  - **⚠️ CRITICAL (file-reference links only): Link target must match actual filename**: The wikilink target (before `|` if present) must be the real filename (minus `.md` suffix), not a "logical name" or "abbreviation" you invent. Always verify the actual filename before constructing the link. If you want a human-friendly display name, use the pipe alias syntax `[[actual-filename|Display Name]]`. Concept/topic links (plain names without `/`) are allowed and are not required to match an existing file.
    - ✅ Good: `[[log-chrome-cdp-phase1-reverse]]` — matches actual filename `log-chrome-cdp-phase1-reverse.md`
    - ✅ Good: `[[log-chrome-cdp-phase1-reverse|Phase 1 逆向能力]]` — pipe alias: target matches filename, display is human-friendly
    - ❌ Bad: `[[chrome-cdp-phase1-reverse]]` — "logical name" that doesn't match the actual filename (missing `log-` prefix)
    - ❌ Bad: `[[phase1]]` — abbreviated name that doesn't match any file
  - **Pipe alias syntax** `[[filename|Display Text]]`: Use when the actual filename is long or not descriptive enough for inline reading. The part before `|` is the link target (must match filename), the part after `|` is the display text.
    - ✅ `[[log-chrome-cdp-phase3-experience|Phase 3 体验完善]]`：target matches file, display is concise
    - ✅ `[[dream-entry-selector.py|入梦提示选择器]]`：target matches file, display is localized
    - ❌ `[[Phase 3 体验完善]]` — no pipe, display text used as target, won't match any file
  - Examples (ordered from preferred to acceptable):
    - ✅ **Best** (shortest & unique): `[[dream-entry-selector.py]]：入梦提示选择脚本`, `[[prs]]：PR 工作流参考`, `[[pr-reviews]]：PR 审查参考`
    - ✅ **Good** (needs prefix for uniqueness): `[[gh-cli/SKILL]]：GitHub CLI skill`, `[[agent-logger/SKILL]]：日志记录 skill`, `[[weread-cli/utils]]：微信读书工具函数`
    - ⚠️ **Acceptable but verbose** (only when shorter name is ambiguous): `[[agent-logger/skills/log-memory-searcher/SKILL]]`
    - ❌ Bad: `[SKILL.md](../../skills/agent-logger/SKILL.md)`, `[helpers.js](src/utils/helpers.js)` — uses file paths
    - ❌ Bad: `[[SKILL]]`, `[[README]]`, `[[utils]]` — not unique, ambiguous targets
    - ❌ Bad: `[[log-memory-searcher/scripts/dream-entry-selector.py]]` — unnecessarily long when `[[dream-entry-selector.py]]` is already unique
- **`.log` directory is the only exception**: Paths within the `.log` directory structure (e.g., `.log/2026/04/13/completed-task.md`) are stable and acceptable, as they are managed by this skill itself
- **Why this matters**: A log entry saying "fixed a bug in `src/utils/helpers.js`" is worthless when that path no longer exists. But "fixed a bug in the `formatDate()` function that caused timezone offset errors" remains useful forever, and the inline code snippet preserves the exact context

### Knowledge Graph Friendly Syntax
Use markdown syntax that supports knowledge graph generation:
- **Tags**: Use graph-compatible tags like `#concept`, `#technology`
- **Links**: Create bidirectional links between related entries
- **Headings**: Use clear hierarchical structure (H1, H2, H3)
- **Lists**: Use bullet points for key takeaways
- **Code blocks**: Include relevant code examples
- **Tables**: Use tables for structured information

### Cross-Language Association
- If content is not in English, add bilingual tags for cross-language linking
- Example: For Chinese content about "React", add tags: `#React #react #前端`
  - `#React` - English tag (capitalized)
  - `#react` - English tag (lowercase, for case-insensitive search)
  - `#前端` - Chinese tag
- This helps knowledge graphs connect documents across languages
- Bilingual tags ensure documents in different languages can reference the same concepts

## Example Log Entry

```yaml
---
title: "Learned about React Hooks"
created: "2026-03-18T20:56:00+08:00"
type: "learning"
author: "<当前AI模型> via <当前Agent平台>"
tags: ["#React", "#Hooks", "#frontend", "#react", "#hooks"]
language: "zh"
---
```

````markdown
# 学习了React Hooks

**Time**: 2026-03-18T20:56:00+08:00

**Tags**: #React #Hooks #frontend

## 我学到了什么

今天我学习了React Hooks，这是一些函数，让你可以在函数组件中使用React的状态和生命周期特性。

### 核心概念

- **useState**: 用于管理组件状态
- **useEffect**: 用于副作用
- **useContext**: 用于消费上下文

### 代码示例

```javascript
const [count, setCount] = useState(0);

useEffect(() => {
  document.title = `Count: ${count}`;
}, [count]);
```

## 相关主题

- [[React Components]]：组件化开发基础
- [[State Management]]：状态管理方案
````

## Log Types

The following are common type references, but not limited to — you can define new types as needed:

| Type | Description | Use When |
|------|-------------|----------|
| `log` | General task completion | Finishing routine tasks |
| `learning` | New knowledge acquired | Learning new technologies or concepts |
| `error` | Mistakes and lessons | Documenting errors and fixes. Use `error_pattern` frontmatter field to classify (e.g., "信息虚构", "流程违规", "修改不完整", "工具盲区") |
| `reflection` | Self-reflection | Thinking about improvements or insights |

## Best Practices

1. **One topic per document**: Focus each log on a single topic for better organization
2. **Protect sensitive information**: Never log passwords, tokens, keys, or credentials - use placeholders instead
3. **Avoid real file paths**: Never log any filesystem paths (absolute or relative) outside `.log` directory - reference code by identity (function/class name + file name) or inline snippets instead
4. **Be specific**: Use clear, descriptive titles
5. **Include context**: Explain why the log entry matters
6. **Add tags**: Use relevant tags for easy retrieval
7. **Link related entries**: Create connections between related logs
8. **Keep it structured**: Use consistent formatting
9. **Document learnings**: Focus on what was learned or achieved
10. **Note improvements**: Record ideas for future improvements

## Wikilink Validation

After writing a log, manually check **file-reference** bidirectional links using `fd`:

> **What to validate**: Only validate links that reference actual files (contain `/` path separator or known skill namespaces like `gh-cli/`, `agent-logger/`). Skip **concept/topic** links (plain names without `/`) — these are forward references that may not have files yet.

> **⚠️ MUST use exact `fd -p` pattern, NEVER use fuzzy keyword search**: Running `fd "keyword"` without `-p` will match any file containing that keyword, giving false confidence that a broken link is valid. Always use the `-p` (full path regex) flag with the anchored pattern shown below.

```bash
# Check a wikilink: convert [[path/to/file]] to fd pattern
# For pipe aliases [[filename|Display Text]], only validate the part before |
# IMPORTANT: Use path separator anchor (\\|/) to avoid false positives (e.g., [[dream-mode]] should not match pr-dream-mode.md)
# (\\|/) is cross-platform: matches \ on Windows and / on Linux/macOS
fd -p "(\\|/)path/to/file.md$" <workspace> --hidden --no-ignore --max-results 5

# Examples:
# [[gh-cli/SKILL]]              →  fd -p "(\\|/)gh-cli(\\|/)SKILL.md$" <workspace> --hidden --no-ignore --max-results 5
# [[ollama-tool-call-demo.ts]]  →  fd -p "(\\|/)ollama-tool-call-demo.ts$" <workspace> --hidden --no-ignore --max-results 5
# [[dream-mode]]                →  fd -p "(\\|/)dream-mode.md$" <workspace> --hidden --no-ignore --max-results 5
# [[log-chrome-cdp-phase1-reverse|Phase 1]]  →  fd -p "(\\|/)log-chrome-cdp-phase1-reverse.md$" <workspace> --hidden --no-ignore --max-results 5
# [[Topic Name]]                →  SKIP (concept link, no file required)
#
# ❌ WRONG — fuzzy keyword search, will give false positives:
# fd "phase1" D:\agentSpace\.log   ← matches ANY file with "phase1" in name, can't detect missing prefix
```

**Interpret results**:
- **1 match**: Link is valid and unique ✅
- **0 matches**: BROKEN — target file doesn't exist or path is wrong ❌
- **2+ matches**: AMBIGUOUS — use more specific path in the link (e.g., `[[gh-cli/SKILL]]` instead of `[[SKILL]]`) ⚠️

**Requirements**: Install `fd` (cross-platform):
- **Windows**: `winget install sharkdp.fd`
- **macOS**: `brew install fd`
- **Linux**: check package manager for `fd-find` or download from GitHub releases

**Pattern rules**:
- **Always add path separator anchor `(\\|/)` before the filename** to avoid false positives (e.g., `dream-mode.md$` would match `pr-dream-mode.md`; `(\\|/)dream-mode.md$` won't). This is cross-platform: matches `\` on Windows and `/` on Linux/macOS
- Replace `/` in wikilink path with `(\\|/)` for cross-platform compatibility
- `.md` files: append `.md$` to the pattern (anchor to filename end, excludes `.bak`, `.old` etc.)
- Non-`.md` files: keep original suffix + `$`
- Always use `--max-results 5` to limit output
- **Always use `--hidden`** to include hidden directories (e.g., `.log/` which stores agent logs)
- **Always use `--no-ignore`** to bypass `.gitignore` rules (workspace may gitignore directories that contain link targets)
- **Regex safety**: If link target contains regex metacharacters (`.`, `(`, `)`, `[`, `]`, `+`, `?`), escape them with `\` in the fd pattern. In practice, wikilink targets rarely contain these characters

## Implementation Notes

- All logs are stored in `<workspace>/.log/` directory
- Each day gets its own nested directory: `<year>/<month>/<day>/`
- Files are named with `log-` prefix for easy identification
- Use absolute paths when creating directories and files
- Ensure proper error handling for file operations
