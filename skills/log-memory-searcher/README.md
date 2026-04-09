# Log Memory Searcher Skill

## 概述

这是一个智能日志回忆与搜索助手，用于帮助用户回忆过去的事件、查找历史记录和整理工作日志。

## 文件结构

```
log-memory-searcher/
├── SKILL.md                      # Skill 定义文件（主要文档）
├── extract-log-metadata.py       # 日志元数据提取脚本
└── README.md                     # 本文件
```

## 快速开始

### 1. 基本用法

当需要回忆或查找日志时，AI 会自动使用此 skill。你也可以手动触发：

```bash
# 进入 skill 目录
cd .lingma/skills/log-memory-searcher/

# 运行脚本（必须指定路径）
python extract-log-metadata.py --path <workspace>/.log/
```

### 2. 常见场景

#### 回忆某个功能
```bash
python extract-log-metadata.py \
  --path ../../../.log/ \
  --search weread chapter \
  --fields title description file_path created
```

#### 查看最近的工作
```bash
python extract-log-metadata.py \
  --path ../../../.log/ \
  --recent-days 7 \
  --fields title description file_path created
```

#### 查找特定时间段
```bash
python extract-log-metadata.py \
  --path ../../../.log/ \
  --from-date 2026-03-01 \
  --to-date 2026-03-31 \
  --fields title description file_path created type
```

## 详细说明

请查看 [SKILL.md](SKILL.md) 获取完整的使用指南、工作流程和最佳实践。

## 依赖

- Python 3.6+
- 无外部依赖（仅使用标准库）

## 维护

- **脚本位置**：`.log/extract-log-metadata.py`（主脚本）
- **Skill 副本**：`.lingma/skills/log-memory-searcher/extract-log-metadata.py`
- **更新策略**：修改主脚本后，记得同步更新 skill 中的副本

```bash
# 同步脚本
copy .log\extract-log-metadata.py .lingma\skills\log-memory-searcher\extract-log-metadata.py
```

## 许可证

MIT License
