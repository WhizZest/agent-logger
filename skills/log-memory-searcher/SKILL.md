---
name: log-memory-searcher
description: 智能日志回忆与搜索助手 - 当需要回忆过去事件、查找历史记录或整理某段时间的工作时使用。通过元数据索引快速定位相关日志文件。支持做梦模式，模拟人类做梦整理记忆的效果。
version: 2.0.0
tags: ["log", "memory", "search", "recall", "metadata", "dream"]
author: Assistant
license: MIT
---

# Log Memory Searcher - 日志回忆与搜索助手

## 触发条件

在以下场景自动使用此 skill：

1. **回忆请求**：用户询问"你还记得xx吗？"、"你回忆一下xx"，但你没有相关记忆或记忆不准确时
2. **历史查找**：用户要求查找某些事情的记录、某个功能的实现过程、某个问题的解决方案等
3. **时间回顾**：用户想了解某段时间做过的事情、某个项目的进展历程等
4. **信息整理**：需要整理分散在多天的相关工作记录时
5. **做梦模式**：用户说"做个梦"、"dream"、"整理一下记忆"等，触发做梦模式，模拟人类做梦整理记忆的效果

## 核心能力

- 📚 **智能检索**：基于 YAML front matter 元数据快速筛选相关日志
- 🔍 **多维度搜索**：支持关键词、时间范围、类型、标签等多条件组合
- 🔗 **关联探索**：自动追踪日志中引用的其他文档或日志
- 📊 **结构化输出**：按时间线或主题整理相关信息
- 🧠 **做梦模式**：模拟人类做梦整理记忆，无目标自由联想，发现隐藏关联，迭代提炼经验

## 工作流程

### 第一步：分析用户需求

理解用户想要回忆/查找的内容，提取关键信息：
- **关键词**：涉及的技术、功能、问题等
- **时间范围**：大概的时间段（如果用户提供）
- **上下文**：相关的背景信息

### 第二步：构建搜索策略

根据需求选择合适的搜索参数：

#### 场景 1：已知关键词
```bash
python <skill_dir>/scripts/extract-log-metadata.py \
  --path <workspace>/.log/ \
  --search <关键词1> <关键词2> \
  --fields title description file_path created type tags
```

#### 场景 2：指定时间范围
```bash
# 最近 N 天
python <skill_dir>/scripts/extract-log-metadata.py \
  --path <workspace>/.log/ \
  --recent-days 7 \
  --fields title description file_path created

# 指定日期范围，如果不指定--to-date，则默认为当前日期
python <skill_dir>/scripts/extract-log-metadata.py \
  --path <workspace>/.log/ \
  --from-date 2026-03-01 \
  --to-date 2026-03-31 \
  --fields title description file_path created
```

#### 场景 3：OR 逻辑搜索（多个同义词）
```bash
python <skill_dir>/scripts/extract-log-metadata.py \
  --path <workspace>/.log/ \
  --search "weread|微信读书|wxread" \
  --fields title description file_path created
```

#### 场景 4：混合逻辑（A或B）且 C
```bash
python <skill_dir>/scripts/extract-log-metadata.py \
  --path <workspace>/.log/ \
  --search "weread|微信读书" \
  --search debug \
  --fields title description file_path created
```

#### 场景 5：浏览所有日志（无明确关键词）
```bash
python <skill_dir>/scripts/extract-log-metadata.py \
  --path <workspace>/.log/ \
  --fields title description file_path created type \
  --limit 20
```

### 第三步：执行搜索并分析结果

1. **运行脚本**：执行 `<skill_dir>/scripts/extract-log-metadata.py` 获取元数据索引
2. **查看索引文件**：读取脚本输出的索引文件（脚本会显示准确的文件路径）
3. **初步筛选**：根据标题、描述、标签判断哪些日志可能相关
4. **调整策略**：如果结果不理想，调整搜索参数重新执行

### 第四步：深入阅读相关日志

对于筛选出的相关日志：
1. **读取完整内容**：使用适当的工具读取日志全文
2. **提取关键信息**：关注问题解决过程、技术方案、经验教训等
3. **"用进废退"原则**：如果认为日志有用、有价值，则添加或更新 YAML front matter 元数据中的`last_accessed` 字段，让该日志不容易随时间而被遗忘，无用的日志则会随时间的推移而被遗忘
   - 获取当前真实时间（ISO 8601 format with timezone），精确到秒，不要毫秒！
   - 如果存在 `last_accessed` 字段，更新其值
   - 如果不存在 `last_accessed` 字段，添加该字段
   - ⚠️ **重要**：必须使用系统当前时间，不要猜测
4. **评估充分性**：如果已获得足够信息，可以停止；如有必要，再按以下方法追踪关联文档：

   > **追踪关联文档方法**：日志正文中可能包含 `[[]]` 双向链接（wikilink）指向其他日志或文件。追踪步骤如下：
   >
   > 1. **提取链接**：从当前日志正文找出所有 `[[]]` 格式的 wikilink
   > 2. **统一用 `fd` 验证**，不做预先分类（如未安装 `fd`，需先安装）：
   >    - **Windows**: `winget install sharkdp.fd`
   >    - **macOS**: `brew install fd`
   >    - **Linux**: 检查包管理器中的 `fd-find` 或从 GitHub releases 下载
   >    ```bash
   >    # 将 [[path/to/file]] 转为 fd 模式
   >    # .md 文件：追加 .md$ 锚定到文件名末尾
   >    # 非 .md 文件：保留原后缀 + $
   >    # 正则安全：若链接目标含正则元字符（. ( ) [ ] + ?），需用 \ 转义（实践中 wikilink 目标很少包含这些字符）
   >
   >    # Windows（路径分隔符用 \\）：
   >    fd -p "path\\to\\file.md$" <workspace> --hidden --max-results 5
   >
   >    # Linux / macOS（路径分隔符用 /）：
   >    fd -p "path/to/file.md$" <workspace> --hidden --max-results 5
   >    ```
   > 3. **根据结果自然分流**：
   >    - **0 匹配** → 目标文件不存在，可能是概念/主题型前向引用，跳过该链接 ❌
   >    - **1 匹配** → 链接有效且唯一，读取目标文档 ✅
   >    - **2+ 匹配** → 歧义！立即修复源日志中的 wikilink，改为更具体的路径（如将 `[[SKILL]]` 改为 `[[gh-cli/SKILL]]`），确保唯一性后再继续 ⚠️
   > 4. **递归深入**：对确认存在的关联文档重复上述过程，直到信息充分或无更多可追踪的文件引用

### 第五步：整理并回答

将找到的信息整理成清晰的回答：
- **时间线**：按时间顺序梳理事件发展
- **关键点**：突出重要的决策、发现、解决方案
- **引用来源**：注明信息来源的日志文件
- **关联信息**：如果有相关文档，一并提供

## 使用示例

### 示例 1：回忆某个功能的实现

**用户**："你还记得微信读书的章节提取是怎么实现的吗？"

**执行**：
```bash
python <skill_dir>/scripts/extract-log-metadata.py \
  --path <workspace>/.log/ \
  --search weread chapter extract \
  --fields title description file_path created tags
```

**分析**：查看索引文件，找到相关日志如：
- "WeRead Chapter Extraction via Outline API"
- "WeRead DOM-based Content Extraction"

然后读取这些日志文件获取详细实现方案。

### 示例 2：查找某段时间的工作

**用户**："我上个月做了哪些工作？"

**执行**：
```bash
python <skill_dir>/scripts/extract-log-metadata.py \
  --path <workspace>/.log/ \
  --from-date 2026-03-01 \
  --to-date 2026-03-31 \
  --fields title description file_path created type
```

**分析**：查看所有日志，按类型分类整理（learning、log、analysis 等）。

### 示例 3：查找问题的解决过程

**用户**："之前遇到的编码问题是怎么解决的？"

**执行**：
```bash
python <skill_dir>/scripts/extract-log-metadata.py \
  --path <workspace>/.log/ \
  --search encoding decode garbled \
  --fields title description file_path created tags
```

**分析**：找到相关日志，读取详细内容了解解决方案。

### 示例 4：追踪某个技术的发展历程

**用户**："CDP 插件系统是怎么一步步开发出来的？"

**执行**：
```bash
python <skill_dir>/scripts/extract-log-metadata.py \
  --path <workspace>/.log/ \
  --search cdp plugin \
  --oldest-first \
  --fields title description file_path created
```

**分析**：按时间顺序（从旧到新）查看所有相关日志，梳理发展历程。

---

## 🧠 做梦模式

做梦模式模拟人类做梦时整理记忆的效果：用户不给出具体指令或目标，Agent 自主在日志间自由联想游走，发现隐藏关联，提炼经验与模式。

**触发词**："做个梦"、"dream"、"整理一下记忆"

**快速概览**：

1. **前置检查**：检查 Git 是否有未提交修改，有则提醒用户先提交
2. **选择入口**：Agent 检查上次梦境的续梦提示；有提示时先用 `extract-log-metadata.py` 搜索候选日志，再调用 `dream-entry-selector.py` 选择入口；无提示时直接调用 `dream-entry-selector.py`
3. **自由联想游走**：通过 wikilink、标签相似度在日志间游走，收集发现
4. **产出三种输出**：
   - ① 修改原始日志（添加带关系类型的 wikilink、补充 description）
   - ② 更新共享梦境报告（跨梦境迭代，保持精炼）
   - ③ 生成独立梦境报告（单次梦境产出）
5. **更新统计**：更新 `stats.yaml` 中沿途日志的 visit_count

**关键约束**：wikilink 必须标注具体关系类型（否则不写入）；偏好与最佳实践冲突时以最佳实践优先；last_accessed 不因做梦而随意更新，仍需遵循"用进废退"原则。

📖 **完整工作流程、输出模板、关系类型参考表、约束详情**：见 [references/dream-mode.md](references/dream-mode.md)

---

## 最佳实践

### 1. 优先使用元数据过滤
- ✅ 先用 `--fields` 限制返回字段，减少数据量
- ✅ 用 `--limit` 限制结果数量，避免信息过载
- ✅ 结合 `--search` 精准定位

### 2. 灵活调整搜索策略
- 如果第一次搜索结果太少 → 放宽关键词或使用 OR 逻辑
- 如果搜索结果太多 → 增加关键词或使用 AND 逻辑
- 如果找不到相关内容 → 尝试同义词或相关概念

### 3. 善用时间范围
- 用户提到"最近" → 使用 `--recent-days 7` 或 `--recent-days 30`
- 用户提到具体月份 → 使用 `--from-date` 和 `--to-date`
- 不确定时间 → 先不限制时间，从结果中判断

### 4. 适度探索关联内容
- 日志中提到的关联文档（双向链接） → 根据需要决定是否查看
- 技术方案的演进 → 如果当前信息已足够，不必追溯所有历史
- 问题的根因分析 → 优先查看直接相关的日志
- **重要原则**：避免无限深入，当信息足够回答问题时即可停止

### 5. 及时更新时间戳
- **何时更新**：阅读日志后认为符合需求，或编辑修改了日志内容
- **如何更新**：获取当前真实时间（ISO 8601 format with timezone），在 YAML front matter 中更新或添加 `last_accessed` 字段
- **重要原则**：必须使用系统当前时间，严禁猜测时间
- **目的**：保持元数据的准确性，便于后续按访问时间排序和筛选

### 6. 输出格式选择
- **默认 MD 格式**：适合人类阅读，结构清晰
- **JSON 格式**：适合程序处理，使用 `--format json`

## 注意事项

⚠️ **路径配置**：
- 默认日志路径为 `<workspace>/.log/`
- 必须使用 `--path` 参数指定路径
- 可以使用相对路径（相对于当前工作目录）或绝对路径

⚠️ **性能考虑**：
- 日志文件较多时，先用 `--limit` 限制数量
- 复杂搜索可以先缩小时间范围
- 避免一次性加载所有日志的完整内容

⚠️ **信息准确性**：
- 元数据中的 `title` 和 `description` 可能不够详细
- 重要信息需要阅读日志全文确认
- 注意日志的时间戳（created vs last_accessed）

⚠️ **时间戳更新**：
- 阅读相关日志后，如果认为符合需求，必须更新或添加 YAML front matter 中的 `last_accessed` 字段
- 编辑修改日志内容后，也必须更新或添加 YAML front matter 中的 `last_accessed` 字段
- 必须获取系统当前真实时间（ISO 8601 format with timezone）
- 严禁猜测时间或使用过期时间

## 附录：<skill_dir>/scripts/extract-log-metadata.py 参数速查

```bash
# 必需参数
--path, -p          指定扫描的日志目录路径

# 字段控制
--fields            指定要提取的字段（默认：title, description, file_path）
--all, -a           提取所有字段

# 搜索过滤
--search, -s        搜索关键词（支持多个，AND 逻辑）
                     使用 | 分隔符实现 OR 逻辑

# 时间范围
--recent-days, -r   最近 N 天
--from-date         起始日期（YYYY-MM-DD）
--to-date           结束日期（YYYY-MM-DD）

# 排序
--oldest-first      从旧到新排序（默认从新到旧）

# 数量限制
--limit, -l         限制结果数量（默认 50，0 表示不限制）

# 输出格式
--format            输出格式：md（默认）或 json

# 调试
--debug, -d         显示详细处理过程
--help              显示帮助信息
```

## 相关技能

- [[agent-logger/SKILL]]：记录新的 agent 日志
- [[everything-search/SKILL]]：根据关键词搜索文档所在路径，仅适用于Windows
