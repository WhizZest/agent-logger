# Log Memory Searcher - 使用指南

## 📖 概述

Log Memory Searcher 是一个智能日志回忆与搜索助手，帮助你快速找到过去的记录、回忆事件细节、整理工作历程。

## 🎯 何时使用

当你需要：
- 🔍 **回忆某件事**："你还记得微信读书的章节提取是怎么实现的吗？"
- 📅 **查找历史记录**："帮我找一下之前解决编码问题的记录"
- 📊 **回顾某段时间**："我上个月做了哪些工作？"
- 🔗 **追踪技术发展**："CDP 插件系统是怎么一步步开发出来的？"

## 🚀 快速开始

### 基本命令

```bash
# 进入 skill 目录
cd .lingma/skills/log-memory-searcher/

# 搜索关键词
python extract-log-metadata.py \
  --path <workspace>/.log/ \
  --search <关键词> \
  --fields title description file_path created
```

### 常见场景

#### 1. 回忆某个功能实现
```bash
python extract-log-metadata.py \
  --path ../../../.log/ \
  --search weread chapter extract \
  --fields title description file_path created tags
```

#### 2. 查看最近的工作
```bash
python extract-log-metadata.py \
  --path ../../../.log/ \
  --recent-days 7 \
  --fields title description file_path created type
```

#### 3. 查找特定时间段
```bash
python extract-log-metadata.py \
  --path ../../../.log/ \
  --from-date 2026-03-01 \
  --to-date 2026-03-31 \
  --fields title description file_path created
```

#### 4. OR 逻辑搜索（同义词）
```bash
python extract-log-metadata.py \
  --path ../../../.log/ \
  --search "weread|微信读书|wxread" \
  --fields title description file_path created
```

## 📋 参数说明

### 必需参数

| 参数 | 短参数 | 说明 | 示例 |
|------|--------|------|------|
| `--path` | `-p` | 日志目录路径 | `--path D:\agentSpace\.log\` |

### 字段控制

| 参数 | 短参数 | 说明 | 默认值 |
|------|--------|------|--------|
| `--fields` | - | 指定要提取的字段 | `title, description, file_path` |
| `--all` | `-a` | 提取所有字段 | - |

### 搜索过滤

| 参数 | 短参数 | 说明 | 示例 |
|------|--------|------|------|
| `--search` | `-s` | 搜索关键词（AND 逻辑） | `--search weread debug` |
| - | - | OR 逻辑用 `\|` 分隔 | `--search "weread\|微信读书"` |

### 时间范围

| 参数 | 短参数 | 说明 | 示例 |
|------|--------|------|------|
| `--recent-days` | `-r` | 最近 N 天 | `--recent-days 7` |
| `--from-date` | - | 起始日期 | `--from-date 2026-03-01` |
| `--to-date` | - | 结束日期 | `--to-date 2026-03-31` |

### 排序与限制

| 参数 | 短参数 | 说明 | 默认值 |
|------|--------|------|--------|
| `--oldest-first` | - | 从旧到新排序 | 从新到旧 |
| `--limit` | `-l` | 限制结果数量 | `50` |

### 输出格式

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--format` | 输出格式：`md` 或 `json` | `md` |

### 其他

| 参数 | 短参数 | 说明 |
|------|--------|------|
| `--debug` | `-d` | 显示详细处理过程 |
| `--help` | - | 显示帮助信息 |

## 💡 使用技巧

### 1. 逐步缩小范围

```bash
# 第一步： broad search
python extract-log-metadata.py -p <path> --search weread --limit 20

# 第二步：添加更多关键词
python extract-log-metadata.py -p <path> --search weread chapter --limit 10

# 第三步：限制时间范围
python extract-log-metadata.py -p <path> --search weread chapter --recent-days 30
```

### 2. 灵活使用 OR 逻辑

```bash
# 搜索多个同义词
python extract-log-metadata.py -p <path> --search "bug|error|issue"

# 混合逻辑：(A 或 B) 且 C
python extract-log-metadata.py -p <path> --search "weread|微信读书" --search debug
```

### 3. 善用默认字段

默认返回 `title`, `description`, `file_path`，足够快速判断相关性。如果需要更多信息，再添加字段：

```bash
# 先看标题和描述
python extract-log-metadata.py -p <path> --search weread

# 觉得需要看标签，再加
python extract-log-metadata.py -p <path> --search weread --fields title description file_path tags
```

### 4. 输出格式选择

- **MD 格式**（默认）：适合人类阅读，结构清晰
- **JSON 格式**：适合程序处理

```bash
# MD 格式
python extract-log-metadata.py -p <path> --search weread

# JSON 格式
python extract-log-metadata.py -p <path> --search weread --format json
```

## 🔍 工作流程

### AI 自动使用流程

1. **分析需求**：理解用户想要回忆/查找的内容
2. **构建搜索**：根据关键词、时间等选择合适的参数
3. **执行搜索**：运行 `extract-log-metadata.py` 获取元数据索引
4. **初步筛选**：查看索引文件，判断哪些日志相关
5. **深入阅读**：读取相关日志的完整内容
6. **追踪关联**：如有必要，继续探索关联文件
7. **整理回答**：按时间线或主题整理信息，注明来源

### 手动使用流程

```bash
# 1. 执行搜索
python extract-log-metadata.py -p <path> --search <keywords>

# 2. 查看生成的索引文件
cat metadata-index.md

# 3. 读取感兴趣的日志文件
cat <workspace>/.log/<file_path>
```

## ⚠️ 注意事项

1. **必须指定路径**：`--path` 是必需参数
2. **相对路径**：相对于当前工作目录
3. **性能优化**：日志多时先用 `--limit` 限制数量
4. **信息准确性**：元数据可能不够详细，需阅读全文确认
5. **脚本同步**：修改主脚本后，记得同步更新 skill 中的副本

## 🔄 维护

### 同步脚本

```bash
# 从主脚本同步到 skill
copy .log\extract-log-metadata.py .lingma\skills\log-memory-searcher\extract-log-metadata.py
```

### 更新 Skill 文档

修改 `SKILL.md` 后，无需特殊操作，AI 会自动加载最新版本。

## 📚 相关资源

- [SKILL.md](SKILL.md) - 完整的 Skill 定义和使用指南
- [README.md](README.md) - Skill 概述和快速开始
- `.log/EXTRACT-METADATA-README.md` - 脚本的详细文档

## 🎓 示例场景

### 场景 1：回忆技术方案

**问题**："微信读书的加密是怎么破解的？"

**步骤**：
```bash
# 1. 搜索相关日志
python extract-log-metadata.py \
  -p ../../../.log/ \
  --search weread encryption decrypt \
  --fields title description file_path created tags

# 2. 查看索引，找到关键日志
# - "WeRead Byte Substitution Encryption Discovery"
# - "WeRead Decryption Function Discovery"

# 3. 读取这些日志了解详细过程
```

### 场景 2：整理项目历程

**问题**："reader-cli 项目是怎么开发的？"

**步骤**：
```bash
# 1. 搜索所有 reader-cli 相关日志，按时间排序
python extract-log-metadata.py \
  -p ../../../.log/ \
  --search reader-cli \
  --oldest-first \
  --fields title description file_path created type

# 2. 按时间线梳理事件发展
# 3. 阅读关键节点的日志了解决策过程
```

### 场景 3：查找问题解决方案

**问题**："之前遇到的 Git 提交错误怎么解决的？"

**步骤**：
```bash
# 1. 搜索 git 相关的问题
python extract-log-metadata.py \
  -p ../../../.log/ \
  --search git error commit \
  --fields title description file_path created

# 2. 查看结果，找到相关的 analysis 类型日志
# 3. 阅读详细内容了解解决方案
```

---

**提示**：AI 会自动使用此 skill，你只需要自然地提出问题即可！
