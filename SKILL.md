---
name: "agent-logger"
description: "Records agent logs with structured markdown files. Invoke when completing complex tasks, learning new knowledge, making serious errors, when self-deemed necessary, or when user requests logging."
---

# Agent Logger

This skill creates structured log entries for the agent to track experiences, learnings, and reflections.

## When to Use

Invoke this skill in these scenarios:
- **After completing a complex task**: When finishing multi-step or non-trivial work
- **When learning new knowledge**: After discovering new technologies, patterns, or insights
- **After making serious errors**: When significant mistakes occur that should be documented for future reference
- **Self-reflection**: When you deem it necessary to record important information
- **User request**: When the user explicitly asks to log something

## Logging Process

### Step 1: Get Current Time
- Get current time in ISO 8601 format with timezone
- Format example: `2026-03-18T20:56:00+08:00`

### Step 2: Create Log Directory
- Check if `<workspace>/.log/<yyyy-MM-dd>/` exists
- If not, create the directory structure
- Example: `D:\agentSpace\.log\2026-03-18\`

### Step 3: Generate Log File
- Create markdown file in the date directory
- File naming format: `<yyyy-MM-dd>-<topic>.md`
- Example: `2026-03-18-completed-task.md`

## Log File Structure

### YAML Frontmatter
```yaml
---
title: "Topic Title" # Always use English for title
created: "2026-03-18T20:56:00+08:00"
type: "log"  # or "learning", "error", "reflection"
tags: ["#tag1", "#tag2", "#tag3"] # Use Obsidian-style tags
language: "zh"  # or "en", etc.
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

### Knowledge Graph Friendly Syntax
Use markdown syntax that supports knowledge graph generation:
- **Tags**: Use Obsidian-style tags like `#concept`, `#technology`
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
tags: ["#React", "#Hooks", "#frontend", "#react", "#hooks"]
language: "zh"
---
```

```markdown
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

- [[React Components]]
- [[State Management]]
```

## Log Types

| Type | Description | Use When |
|------|-------------|----------|
| `log` | General task completion | Finishing routine tasks |
| `learning` | New knowledge acquired | Learning new technologies or concepts |
| `error` | Mistakes and lessons | Documenting errors and fixes |
| `reflection` | Self-reflection | Thinking about improvements or insights |

## Best Practices

1. **One topic per document**: Focus each log on a single topic for better organization
2. **Protect sensitive information**: Never log passwords, tokens, keys, or credentials - use placeholders instead
3. **Be specific**: Use clear, descriptive titles
4. **Include context**: Explain why the log entry matters
5. **Add tags**: Use relevant tags for easy retrieval
6. **Link related entries**: Create connections between related logs
7. **Keep it structured**: Use consistent formatting
8. **Document learnings**: Focus on what was learned or achieved
9. **Note improvements**: Record ideas for future improvements

## Implementation Notes

- All logs are stored in `<workspace>/.log/` directory
- Each day gets its own subdirectory
- Files are named with date prefix for easy sorting
- Use absolute paths when creating directories and files
- Ensure proper error handling for file operations
