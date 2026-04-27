# 做梦模式参考文档

## 目录

- [做梦模式参考文档](#做梦模式参考文档)
  - [目录](#目录)
  - [核心理念](#核心理念)
  - [目录结构](#目录结构)
  - [入梦提示集](#入梦提示集)
    - [提示类型](#提示类型)
    - [数据格式](#数据格式)
    - [字段说明](#字段说明)
    - [选择算法](#选择算法)
    - [维护方式](#维护方式)
    - [创建规范](#创建规范)
  - [工作流程](#工作流程)
    - [第一步：前置检查](#第一步前置检查)
    - [第二步：选择入梦提示](#第二步选择入梦提示)
    - [第三步：选择入口](#第三步选择入口)
      - [情况 A：task 型提示](#情况-atask-型提示)
      - [情况 B：perspective 型提示](#情况-bperspective-型提示)
      - [情况 C：无提示](#情况-c无提示)
    - [第四步：游走 / 分析](#第四步游走--分析)
      - [task 型：系统性分析](#task-型系统性分析)
      - [perspective 型：带视角的自由联想](#perspective-型带视角的自由联想)
      - [无提示：纯自由联想](#无提示纯自由联想)
    - [第五步：产出四种输出](#第五步产出四种输出)
      - [输出①：修改原始日志](#输出修改原始日志)
      - [输出②（可选）：更新或创建 AGENTS.md](#输出可选更新或创建-agentsmd)
      - [输出③：生成独立梦境报告](#输出生成独立梦境报告)
      - [输出④：追加续梦提示（可选）](#输出追加续梦提示可选)
    - [第六步：更新统计](#第六步更新统计)
  - [做梦模式的约束](#做梦模式的约束)
  - [脚本参数速查](#脚本参数速查)
    - [dream-hint-selector.py](#dream-hint-selectorpy)
    - [dream-entry-selector.py](#dream-entry-selectorpy)

## 核心理念

- **无目的漫游**：不需要用户给具体目标，自主浏览
- **随机关联**：通过 wikilink 跳转、标签邻近性做自由联想
- **记忆巩固**：强化重要连接，弱化无关内容
- **模式浮现**：在自由浏览中发现跨日志的隐藏规律
- **碎片重组**：把不同时间、不同主题的日志拼出新的洞见
- **可迭代的记忆**：每次做梦留下痕迹，影响下次做梦的方向
- **入梦提示**：可复用的分析视角或结构化任务，让做梦不只是漫无目的地游走

## 目录结构

```
<workspace>/
├── AGENTS.md                        ← Agent 上下文文件（跨梦境迭代，也可手动编辑）
├── .log/
│   ├── 2026/                        ← 原始日志（年/月/日 三层嵌套结构）
│   │   ├── 04/
│   │   │   ├── 22/...
│   │   │   └── 23/...
│   │   └── ...
│   └── dreams/                      ← 做梦模式专属目录
│       ├── dream-hints.yaml         ← 入梦提示集（可复用 + 一次性续梦提示）
│       ├── stats.yaml               ← 统计文件（只记录被梦到过的日志）
│       └── 2026/                    ← 梦境报告（年/月/日 三层嵌套结构）
│           └── 04/
│               ├── 22/
│               │   └── dream-1.md   ← 独立梦境报告
│               └── 23/
│                   └── dream-1.md   ← 独立梦境报告
```

## 入梦提示集

入梦提示集存放在 `<workspace>/.log/dreams/dream-hints.yaml`，统一管理所有入梦提示，包括可复用的持久提示和一次性的续梦提示。

### 提示类型

| 类型 | 说明 | 游走方式 |
|------|------|----------|
| `task` | 结构化分析，暗含工作流程 | 系统性遍历搜索结果 |
| `perspective` | 自由联想 + 视角 | 自由游走，关注提示主题 |

### 数据格式

```yaml
hints:
  - type: task
    description: "检索所有 error 日志，看错误是否随时间降低，哪些屡教不改"
    cooldown_days: 7
    priority: 3
    last_used: null

  - type: task
    description: "检索所有 learning 日志，看是否有重复学习"
    cooldown_days: 14
    priority: 2
    last_used: "2026-04-20T08:00:00+08:00"

  - type: perspective
    description: "游走时关注性能相关的内容和模式"
    cooldown_days: 3
    priority: 1
    last_used: null

  - type: perspective
    description: "继续探索数据库优化和日志压缩的关联"
    cooldown_days: 0
    priority: 3
    last_used: null
    disposable: true
```

### 字段说明

| 字段 | 必需 | 说明 |
|------|------|------|
| `type` | 是 | `task` 或 `perspective` |
| `description` | 是 | 提示内容，自然语言描述，同时作为唯一标识 |
| `cooldown_days` | 是 | 冷却天数，0 表示无冷却 |
| `priority` | 是 | 优先级数值，正整数，推荐 1-3 |
| `last_used` | 是 | 上次使用时间（ISO 8601），null 表示未使用过 |
| `disposable` | 否 | 默认 false。true 表示用一次后自动删除（即续梦提示） |

### 选择算法

1. **过滤**：排除冷却期内的提示
2. **计算权重**：
   - `cooldown_days > 0`：`weight = priority × (1 + days_since_cooldown / cooldown_days)`
     - `last_used` 为 null 时：`days_since_cooldown = cooldown_days`（相当于刚过冷却期）
   - `cooldown_days == 0`（disposable 提示）：`weight = priority`（常数）
   - "无提示"选项：固定权重 = 2
3. **按权重随机选择**
4. **更新状态**：选中提示的 `last_used` 更新为当前时间；`disposable: true` 的提示自动删除

### 维护方式

- **手动编辑**：用户可直接编辑 `dream-hints.yaml`
- **通过 Agent**：用户说"添加一个入梦提示"、"管理入梦提示"等，Agent 负责编辑文件
- **做梦产出**：做梦过程中如果有续梦意图，自动追加 `disposable: true` 的提示

### 创建规范

当 `dream-hints.yaml` 不存在时，`dream-hint-selector.py` 直接输出"无提示"。首次创建文件格式：

```yaml
hints: []
```

或包含初始提示：

```yaml
hints:
  - type: task
    description: "检索所有 error 日志，看错误是否随时间降低，哪些屡教不改"
    cooldown_days: 7
    priority: 3
    last_used: null
```

## 工作流程

### 第一步：前置检查

检查 Git 是否有未提交的修改或新文件：

```bash
git status --short
```

- 如果有未提交的修改 → **提醒用户先提交**，因为做梦模式会修改原始日志
- 如果工作区干净 → 继续下一步

### 第二步：选择入梦提示

运行入梦提示选择器：

```bash
python <skill_dir>/scripts/dream-hint-selector.py \
  --dreams-path <workspace>/.log/dreams/
```

脚本输出：
- **选中提示**：描述、类型（task/perspective）
- **无提示**：自由联想

### 第三步：选择入口

根据第二步的结果，选择对应流程：

#### 情况 A：task 型提示

1. **Agent 从提示中提取搜索条件**：例如提示"检索所有 error 日志"，Agent 提取关键词 `error`
2. **搜索相关日志**：

```bash
python <skill_dir>/scripts/extract-log-metadata.py \
  --path <workspace>/.log/ \
  --search "error" \
  --fields file_path \
  --format json \
  --limit 0
```

3. **系统性遍历搜索结果**（不需要 `dream-entry-selector.py`）

#### 情况 B：perspective 型提示

1. **Agent 从提示中提取关键词**：例如提示"关注性能相关的内容"，Agent 提取关键词 `性能|performance|优化`
2. **搜索候选日志**：

```bash
python <skill_dir>/scripts/extract-log-metadata.py \
  --path <workspace>/.log/ \
  --search "性能|performance|优化" \
  --fields file_path \
  --format json \
  --limit 0
```

3. **选择入口**：

```bash
python <skill_dir>/scripts/dream-entry-selector.py \
  --log-path <workspace>/.log/ \
  --dreams-path <workspace>/.log/dreams/ \
  --hint-candidates <workspace>/.log/metadata-index.json \
  --fields title,description,tags
```

#### 情况 C：无提示

直接运行入口选择脚本：

```bash
python <skill_dir>/scripts/dream-entry-selector.py \
  --log-path <workspace>/.log/ \
  --dreams-path <workspace>/.log/dreams/ \
  --fields title,description,tags
```

入口选择算法：
- **首次做梦**：100% 随机选择
- **有统计但无续梦候选**：40% 偏向被梦到少的 + 60% 随机
- **有统计且有续梦候选**：40% 偏向被梦到少的 + 30% 续梦候选引导 + 30% 随机

偏向"被梦到少"的具体实现：取 visit_count 最低的前 20% 日志，使用逆权重采样（权重 = 1/(visit_count+1)），次数越少概率越高。

### 第四步：游走 / 分析

根据提示类型，采用不同的游走方式：

#### task 型：系统性分析

1. 按顺序遍历第三步搜索到的日志
2. 针对提示描述的分析任务，逐条提取相关信息
3. 汇总分析结果，形成结论

#### perspective 型：带视角的自由联想

1. 从入口日志开始，在日志间自由联想游走
2. 游走时额外关注与提示主题相关的内容
3. 发现与提示主题相关的关联时优先追踪

#### 无提示：纯自由联想

1. 从入口日志开始，在日志间自由联想游走
2. 选择下一步方向：
   - 当前日志中的 wikilink → 跳转到关联日志
   - 标签相似度 → 跳转到有相似标签的其他日志
   - 做梦统计偏向 → 偏向被梦到少的日志
3. 收集沿途发现

**通用规则**：
- 至少走 3-5 步，避免太浅
- 当前路径是否还在产生新洞见？如果连续几步都是已知信息，考虑换方向或结束
- 是否有足够的收获来形成有深度的报告？

⚠️ **游走范围**：path_visited 不限于日志文件，也可能经过代码文件、配置文件等非日志文档。但非日志文档不参与统计，一般不修改，如有修改建议写入独立梦境报告。

### 第五步：产出四种输出

#### 输出①：修改原始日志

在游走过程中，如果发现确实需要修改原始日志：

**添加 wikilink**：发现日志 A 和日志 B 有关联时，必须能指明具体的关系类型。关系类型是开放列表，常见参考：

| 关系类型 | 含义 | 示例 |
|---------|------|------|
| 对比/比较 | 两者可对比 | `[[B]]（对比/比较）` |
| 前置知识 | A 需要 B 的知识 | `[[B]]（前置知识）` |
| 导致/原因 | B 导致了 A | `[[B]]（导致/原因）` |
| 解决 | B 解决了 A 中的问题 | `[[B]]（解决）` |
| 组成部分 | B 是 A 的一部分 | `[[B]]（组成部分）` |
| 参考阅读 | B 是 A 的参考 | `[[B]]（参考阅读）` |
| 依赖 | A 依赖 B | `[[B]]（依赖）` |
| 演进/迭代 | A 是 B 的演进版本 | `[[B]]（演进/迭代）` |
| 替代方案 | B 是 A 的替代 | `[[B]]（替代方案）` |
| 补充说明 | B 补充了 A | `[[B]]（补充说明）` |

⚠️ **置信度要求**：写入 wikilink 需要满足两个条件：
1. **能指明具体关系类型**：如果无法指明，说明关联置信度不够
2. **关联有实质意义**：不是表面相似，而是核心内容确实相关，对读者有实际价值

**反例**：两篇日志都涉及"问题诊断"，但场景和方法差异很大 → 关联牵强，不应写入

**补充/更新 description**：
- 如果 description 为空或不准确 → 值得补充更新
- 如果标题已足够说明日志内容 → 不需要 description

**合规性检查**：对照 [[agent-logger/SKILL|agent-logger skill]] 的当前规范，检查本次游走路径中访问到的日志是否合规，不合规的按新规范修改。常见检查项：
- frontmatter 格式和字段完整性
- wikilink 是否有描述
- 是否使用了文件路径而非 wikilink
- 标签格式是否规范
- 是否混入敏感信息
- 是否违反单主题原则

#### 输出②（可选）：更新或创建 AGENTS.md

`AGENTS.md` 存放在 workspace 根目录，是 Agent 的上下文输入文件。内容必须精炼、准确、泛用——每条信息对 Agent 都有实际指导意义，不应有多余文本。

该文件可由做梦模式迭代更新，也可由用户手动编辑。不需要区分来源。

仅当本次做梦确实发现了跨场景的通用信息，或发现已有内容不再适用时，才更新 AGENTS.md。没有实质更新时不要强行修改。内容原则：
- **精炼**：每条信息必须可操作，不是冗长叙述或原始日志复述
- **准确**：发现之前的内容不再适用时，移除并在独立梦境报告中说明
- **泛用**：只保留跨场景通用的信息，场景特定的写在独立梦境报告中

分区结构是开放列表，以下为参考。有内容才保留标题，没有内容的分区不保留空标题。

```markdown
## 用户画像

有利于 Agent 与用户协作交互的偏好和特征。
当"偏好"与最佳实践冲突时，以最佳实践为优先。

- 技术栈偏好：...
- 工作风格：...

## 广泛适用的原则

- 原则1：...（首次提炼于 #N 梦境，迭代于 #M 梦境）

## 通用经验与模式

- ...

## 通用工作流

- ...

## 通用最佳实践

- ...

## 关键认知

- ...
```

**降级机制**：如果发现之前认为"广泛适用"的原则其实只是场景特定的，从 AGENTS.md 移除，并在独立梦境报告中说明移除原因。

#### 输出③：生成独立梦境报告

独立梦境报告存放在 `<workspace>/.log/dreams/<yyyy>/<MM>/<dd>/dream-<N>.md`，每次做梦独立产出。

```markdown
---
type: dream
created: <当前时间>
dream_id: <梦境编号>
entry_log: <入口日志路径>
hint_description: <入梦提示描述，无提示则为 null>
hint_type: <task/perspective/null>
path_visited:
  - "<路径1>"
  - "<路径2>"
  - "<路径3>"
---

# 梦境报告 #<编号>

## 游走路径

- 入口 → A → B → C → ...

## 发现的关联

- A 与 B 之间存在 XX 关系：...
- ...

## 场景特定的经验

只适用于特定场景的原则、经验、工作流、模式、习惯、规范、最佳实践、关键认知等。

- ...

## 偏好与最佳实践

当发现用户偏好与最佳实践冲突时，在此标注，供与用户讨论。

- 用户倾向 XX，但最佳实践是 YY：...

## Skill 建议

- 可提炼为新 skill：...
- 可更新现有 skill：...

## 续梦意图（可选）

如果有续梦意图，请同步添加到 `dream-hints.yaml`。无续梦意图则省略此节。
- 续梦描述：...

## 修改的日志（可选）

1. [[日志1]] 修改内容：...
2. [[日志2]] 修改内容：...
3. [[日志3]] 修改内容：...
```

#### 输出④：追加续梦提示（可选）

⚠️ 本步骤是可选的，仅在做梦过程中确实产生了续梦意图时执行。

如果做梦过程中产生了续梦意图，追加一条 `disposable: true` 的提示到 `dream-hints.yaml`：

1. 读取 `dream-hints.yaml`
2. 追加新提示：
```yaml
  - type: perspective
    description: "<续梦描述>"
    cooldown_days: 0
    priority: 3
    last_used: null
    disposable: true
```
3. 保存文件

⚠️ 续梦提示的 `priority` 由 Agent 根据实际情况灵活决定，`cooldown_days` 固定为 0。

### 第六步：更新统计

入口选择脚本已自动更新 `stats.yaml`。如果在游走过程中访问了其他日志，也需要手动更新统计：

- 读取 `<workspace>/.log/dreams/stats.yaml`
- 为 path_visited 中的每个日志路径增加 visit_count
- 更新 last_dreamed 时间戳
- 保存文件

⚠️ **统计文件只记录被梦到过的日志**，未被梦到的不需要记录，因此不存在新日志同步问题。

## 做梦模式的约束

1. **wikilink 需满足两个条件**：①能指明具体关系类型；②关联有实质意义（不是表面相似）
2. **偏好与最佳实践冲突时，以最佳实践为优先**：强化"好"的偏好（共享报告），暴露"不好"的供讨论（独立报告）
3. **共享报告保持精炼**：降级时直接移除，不标注
4. **非日志文档不参与统计，一般不修改**：修改建议写入独立报告
5. **默认不写新日志**：梦境报告放在 `dreams/` 目录，与日志区分
6. **last_accessed 不因做梦而更新**：做梦的统计使用独立的 `stats.yaml`，不污染原始日志的 `last_accessed` 字段
7. **原始日志受 Git 保护**：做梦前检查 Git 状态，有未提交修改则提醒用户先提交

## 脚本参数速查

### dream-hint-selector.py

```bash
# 必需参数
--dreams-path       梦境目录路径（必需）

# 可选参数
--debug, -d         显示详细调试信息
--help              显示帮助信息
```

### dream-entry-selector.py

```bash
# 必需参数
--log-path          日志目录路径（必需）
--dreams-path       梦境目录路径（必需）

# 可选参数
--hint-candidates   续梦候选日志的 JSON 文件路径（由 extract-log-metadata.py 生成）
                    例如: --hint-candidates <workspace>/.log/metadata-index.json
--fields, -f        要输出的额外字段，逗号分隔
                    例如: --fields title,description,tags
--debug, -d         显示详细调试信息
--help              显示帮助信息
```
