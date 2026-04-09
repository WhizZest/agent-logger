# Agent Logger Skills / 智能体日志技能集

<details open>
<summary>🇨🇳 查看中文版本 (View Chinese Version)</summary>

# 智能体日志技能集

一组用于日志记录、记忆管理和历史记录检索的 AI 智能体技能。

## 📦 可用技能

### 1. agent-logger（智能体日志记录器）
使用结构化的 Markdown 文件记录智能体日志。在完成复杂任务、学习新知识、出现严重错误、被用户纠正或明确请求时自动调用。

**位置：** `skills/agent-logger/`

### 2. log-memory-searcher（日志回忆与搜索助手）
智能日志回忆与搜索助手。通过元数据索引帮助检索过去事件、搜索历史记录和整理工作日志。

**特性：**
- 智能触发条件，适用于记忆回忆场景
- 多维度搜索（关键词、时间范围、标签、类型）
- 灵活的搜索策略，支持 AND/OR 逻辑
- 基于元数据的快速筛选
- 时间范围过滤（最近 N 天、指定日期范围）
- 可配置的字段选择和结果数量限制

**位置：** `skills/log-memory-searcher/`

## 🏗️ 目录结构

每个技能遵循标准格式：

```
skill-name/
├── SKILL.md              # 必需 - 包含 YAML frontmatter 的主要指令
└── scripts/              # 可选 - 可执行代码
    └── script.py         # 工具脚本
```

## 🚀 使用方法

这些技能遵循主流 AI 智能体框架的标准规范，可以：

1. **克隆仓库**：`git clone https://github.com/WhizZest/agent-logger.git`
2. **创建符号链接**：将技能链接到智能体的 skills 目录
   
   **Linux/macOS:**
   ```bash
   # 对于 .agents/skills/ 目录
   ln -s /path/to/agent-logger/skills/log-memory-searcher ~/.agents/skills/
   
   # 或对于其他平台的 skills 目录
   ln -s /path/to/agent-logger/skills/log-memory-searcher <platform>/skills/
   ```
   
   **Windows (PowerShell):**
   ```powershell
   # 对于 .agents/skills/ 目录
   New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.agents\skills\log-memory-searcher" -Target "D:\path\to\agent-logger\skills\log-memory-searcher"
   
   # 或对于其他平台的 skills 目录
   New-Item -ItemType SymbolicLink -Path "<platform>\skills\log-memory-searcher" -Target "D:\path\to\agent-logger\skills\log-memory-searcher"
   ```
   
   **注意**：Windows 上创建符号链接可能需要管理员权限。
   
3. **集中管理**：通过符号链接实现单一数据源，多处使用

## 📝 开发指南

### 添加新技能

1. 在 `skills/` 下创建新目录
2. 添加带有正确 YAML frontmatter 的 `SKILL.md`
3. 在 `scripts/` 目录中包含必要的脚本
4. 遵循 `create-skill` 或其他智能体框架的技能创建指南

### 技能规范

- 保持 `SKILL.md` 正文在 500 行以内
- 对详细内容使用渐进式披露
- 使用第三人称编写描述，包含清晰的触发条件
- 避免额外的文档文件（技能内不要有 README.md、USAGE.md）
- 将可重用资源组织在 `scripts/`、`references/` 或 `assets/` 目录中

</details>

<details>
<summary>🇺🇸 View English Version (查看英文版本)</summary>

A collection of AI agent skills for logging, memory management, and historical record retrieval.

## 📦 Available Skills

### 1. agent-logger
Records agent logs with structured markdown files. Automatically invoked when completing complex tasks, learning new knowledge, making serious errors, being corrected by users, or when explicitly requested.

**Location:** `skills/agent-logger/`

### 2. log-memory-searcher
Intelligent log recall and search assistant. Helps retrieve past events, search historical records, and organize work logs through metadata indexing.

**Features:**
- Smart trigger conditions for memory recall scenarios
- Multi-dimensional search (keywords, time range, tags, types)
- Flexible search strategies with AND/OR logic
- Metadata-based filtering for quick log identification
- Time range filtering (recent days, date range)
- Configurable field selection and result limiting

**Location:** `skills/log-memory-searcher/`

## 🏗️ Structure

Each skill follows the standard skill format:

```
skill-name/
├── SKILL.md              # Required - main instructions with YAML frontmatter
└── scripts/              # Optional - executable code
    └── script.py         # Utility scripts
```

## 🚀 Usage

These skills follow standard specifications for mainstream AI agent frameworks and can be:

1. **Clone repository**: `git clone https://github.com/WhizZest/agent-logger.git`
2. **Create symlinks**: Link skills to your agent's skills directory
   
   **Linux/macOS:**
   ```bash
   # For .agents/skills/ directory
   ln -s /path/to/agent-logger/skills/log-memory-searcher ~/.agents/skills/
   
   # Or for other platform's skills directories
   ln -s /path/to/agent-logger/skills/log-memory-searcher <platform>/skills/
   ```
   
   **Windows (PowerShell):**
   ```powershell
   # For .agents/skills/ directory
   New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.agents\skills\log-memory-searcher" -Target "D:\path\to\agent-logger\skills\log-memory-searcher"
   
   # Or for other platform's skills directories
   New-Item -ItemType SymbolicLink -Path "<platform>\skills\log-memory-searcher" -Target "D:\path\to\agent-logger\skills\log-memory-searcher"
   ```
   
   **Note**: Creating symbolic links on Windows may require administrator privileges.
   
3. **Centralized management**: Use symlinks for single source of truth across multiple locations

## 📝 Development

### Adding a New Skill

1. Create a new directory under `skills/`
2. Add `SKILL.md` with proper YAML frontmatter
3. Include any necessary scripts in `scripts/` directory
4. Follow skill creation guidelines from `create-skill` or other agent frameworks

### Skill Guidelines

- Keep `SKILL.md` body under 500 lines
- Use progressive disclosure for detailed content
- Write descriptions in third person with clear trigger conditions
- Avoid extraneous documentation files (no README.md, USAGE.md within skills)
- Organize reusable resources in `scripts/`, `references/`, or `assets/` directories

</details>
