#!/usr/bin/env python3
"""
做梦模式入口选择器
根据日志 front matter 中的做梦统计和续梦提示，选择下次做梦的入口日志

统计数据存储在日志文件的 YAML front matter 中：
  - dream_visit_count: 被梦到的次数
  - last_dreamed: 上次被梦到的时间

使用方法:
    python dream-entry-selector.py --log-path <workspace>/.log/ --dreams-path <workspace>/.log/dreams/
    python dream-entry-selector.py --log-path <workspace>/.log/ --dreams-path <workspace>/.log/dreams/ --hint-candidates metadata-index.json
    python dream-entry-selector.py --log-path <workspace>/.log/ --dreams-path <workspace>/.log/dreams/ --fields title,description,file_path
    python dream-entry-selector.py --log-path <workspace>/.log/ --dreams-path <workspace>/.log/dreams/ --debug
"""

import sys
import json
import re
import argparse
import random
from pathlib import Path
from datetime import datetime, timezone


def extract_yaml_frontmatter(content):
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return None

    yaml_content = match.group(1)
    metadata = {}

    lines = yaml_content.split('\n')
    current_key = None
    current_value = []
    in_array = False

    for line in lines:
        kv_match = re.match(r'^(\w+):\s*(.*)', line)

        if kv_match:
            if current_key and in_array:
                array_str = '\n'.join(current_value)
                array_match = re.search(r'\[(.*)\]', array_str, re.DOTALL)
                if array_match:
                    items_str = array_match.group(1)
                    items = [item.strip().strip('"').strip("'") for item in items_str.split(',') if item.strip()]
                    metadata[current_key] = items

            current_key = kv_match.group(1).strip()
            current_value = [kv_match.group(2).strip()]

            if '[' in kv_match.group(2) and ']' not in kv_match.group(2):
                in_array = True
            elif '[' in kv_match.group(2) and ']' in kv_match.group(2):
                array_match = re.search(r'\[(.*)\]', kv_match.group(2))
                if array_match:
                    items_str = array_match.group(1)
                    items = [item.strip().strip('"').strip("'") for item in items_str.split(',') if item.strip()]
                    metadata[current_key] = items
                else:
                    value = kv_match.group(2).strip().strip('"').strip("'")
                    metadata[current_key] = value
                current_key = None
                in_array = False
            else:
                value = kv_match.group(2).strip().strip('"').strip("'")
                metadata[current_key] = value
                current_key = None
                in_array = False
        elif in_array and current_key:
            current_value.append(line)

    if current_key and in_array:
        array_str = '\n'.join(current_value)
        array_match = re.search(r'\[(.*)\]', array_str, re.DOTALL)
        if array_match:
            items_str = array_match.group(1)
            items = [item.strip().strip('"').strip("'") for item in items_str.split(',') if item.strip()]
            metadata[current_key] = items

    return metadata


def update_frontmatter_fields(file_path, fields):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    frontmatter_match = re.match(r'^(---\s*\n)(.*?)(\n---)', content, re.DOTALL)
    if not frontmatter_match:
        return False

    opening = frontmatter_match.group(1)
    yaml_content = frontmatter_match.group(2)
    closing = frontmatter_match.group(3)
    body = content[frontmatter_match.end():]

    for field_name, field_value in fields:
        field_pattern = re.compile(r'^(' + re.escape(field_name) + r':\s*).*$', re.MULTILINE)
        if field_pattern.search(yaml_content):
            yaml_content = field_pattern.sub(r'\g<1>' + field_value, yaml_content)
        else:
            yaml_content = yaml_content.rstrip('\n') + '\n' + field_name + ': ' + field_value

    new_content = opening + yaml_content + closing + body

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True


def _iter_dream_files(dreams_path, reverse=False):
    if not dreams_path.exists():
        return
    dream_files = sorted(
        (f for f in dreams_path.rglob('dream-*.md')
         if re.match(r'dream-(?!\d)', f.stem)),
        reverse=reverse,
    )
    yield from dream_files


def get_dream_count(dreams_path):
    return sum(1 for _ in _iter_dream_files(dreams_path))


def weighted_random_choice(candidates, weights):
    total = sum(weights)
    if total <= 0:
        return random.choice(candidates)

    r = random.uniform(0, total)
    cumulative = 0
    for candidate, weight in zip(candidates, weights):
        cumulative += weight
        if r <= cumulative:
            return candidate

    return candidates[-1]


def _load_hint_candidates(candidates_path):
    if not candidates_path or not candidates_path.exists():
        return []
    try:
        with open(candidates_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        return [item.get('file_path', '') for item in data if item.get('file_path')]
    except Exception:
        return []


def select_entry(log_dir, dreams_path, hint_candidates=None, fields=None, debug=False, dry_run=False):
    dream_count = get_dream_count(dreams_path)

    if debug:
        print(f"[DEBUG] 已有梦境次数: {dream_count}")
        if hint_candidates:
            print(f"[DEBUG] 续梦候选日志数: {len(hint_candidates)}")

    md_files = sorted(log_dir.rglob('*.md'))
    dreams_dir_files = set()
    if dreams_path.exists():
        for f in dreams_path.rglob('*.md'):
            try:
                dreams_dir_files.add(f.relative_to(log_dir))
            except ValueError:
                pass

    log_entries = []
    for file_path in md_files:
        try:
            rel_path = file_path.relative_to(log_dir)
        except ValueError:
            continue

        if rel_path in dreams_dir_files:
            continue

        rel_path_str = str(rel_path).replace('\\', '/')

        if rel_path_str.startswith('dreams/'):
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            metadata = extract_yaml_frontmatter(content)
        except Exception:
            metadata = None

        if not metadata:
            continue

        metadata['file_path'] = rel_path_str

        visit_count = 0
        if 'dream_visit_count' in metadata:
            try:
                visit_count = int(metadata['dream_visit_count'])
            except (ValueError, TypeError):
                visit_count = 0

        log_entries.append({
            'path': rel_path_str,
            'abs_path': file_path,
            'metadata': metadata,
            'visit_count': visit_count,
        })

    if not log_entries:
        print("错误: 未找到任何日志文件", file=sys.stderr)
        sys.exit(1)

    if debug:
        print(f"[DEBUG] 可选日志数量: {len(log_entries)}")
        visit_counts = [e['visit_count'] for e in log_entries]
        print(f"[DEBUG] 访问次数分布: min={min(visit_counts)}, max={max(visit_counts)}, "
              f"avg={sum(visit_counts)/len(visit_counts):.1f}")

    if dream_count == 0:
        selected = random.choice(log_entries)
        reason = "首次做梦，随机选择"
    else:
        sorted_entries = sorted(log_entries, key=lambda x: x['visit_count'])
        top_n = max(1, len(sorted_entries) * 20 // 100)
        low_visit_pool = sorted_entries[:top_n]

        low_visit_weights = [1.0 / (e['visit_count'] + 1) for e in low_visit_pool]

        hint_entries = []
        if hint_candidates:
            candidate_set = set(hint_candidates)
            hint_entries = [e for e in log_entries if e['path'] in candidate_set]

        has_hint = len(hint_entries) > 0

        if has_hint:
            w_low = 0.4
            w_hint = 0.3
            w_random = 0.3
        else:
            w_low = 0.4
            w_hint = 0.0
            w_random = 0.6

        roll = random.random()
        if roll < w_low:
            selected = weighted_random_choice(low_visit_pool, low_visit_weights)
            reason = f"偏向被梦到少的日志（被梦到 {selected['visit_count']} 次）"
        elif roll < w_low + w_hint:
            selected = random.choice(hint_entries)
            reason = "续梦候选引导"
        else:
            selected = random.choice(log_entries)
            reason = "随机探索"

    now = datetime.now().astimezone().isoformat(timespec='seconds')
    new_count = selected['visit_count'] + 1
    if not dry_run:
        update_frontmatter_fields(selected['abs_path'], [
            ('dream_visit_count', str(new_count)),
            ('last_dreamed', f'"{now}"'),
        ])

    if debug:
        if dry_run:
            print(f"[DEBUG] [DRY-RUN] 将更新日志 front matter: {selected['path']} (visit_count={new_count})")
        else:
            print(f"[DEBUG] 已更新日志 front matter: {selected['path']} (visit_count={new_count})")

    result = {
        'entry_path': selected['path'],
        'reason': reason,
        'dream_count': dream_count + 1,
    }

    if fields:
        for field in fields:
            field = field.strip()
            if field in selected['metadata']:
                result[f'entry_{field}'] = selected['metadata'][field]

    return result


def main():
    parser = argparse.ArgumentParser(description='做梦模式入口选择器')
    parser.add_argument('--log-path', type=str, required=True,
                        help='日志目录路径（必需）')
    parser.add_argument('--dreams-path', type=str, required=True,
                        help='梦境目录路径（必需）')
    parser.add_argument('--hint-candidates', type=str, default='',
                        help='续梦候选日志的 JSON 文件路径（由 extract-log-metadata.py 生成），例如: --hint-candidates metadata-index.json')
    parser.add_argument('--fields', '-f', type=str, default='',
                        help='要输出的额外字段，逗号分隔，例如: --fields title,description,tags')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='显示详细调试信息')
    parser.add_argument('--dry-run', action='store_true',
                        help='只选择入口，不写入 front matter（测试用）')
    args = parser.parse_args()

    log_dir = Path(args.log_path)
    if not log_dir.is_absolute():
        log_dir = Path.cwd() / log_dir

    dreams_path = Path(args.dreams_path)
    if not dreams_path.is_absolute():
        dreams_path = Path.cwd() / dreams_path

    if not log_dir.exists():
        print(f"错误: 日志目录不存在: {log_dir}", file=sys.stderr)
        sys.exit(1)

    dreams_path.mkdir(parents=True, exist_ok=True)

    fields = [f.strip() for f in args.fields.split(',') if f.strip()] if args.fields else None
    hint_candidates = _load_hint_candidates(Path(args.hint_candidates)) if args.hint_candidates else None

    result = select_entry(log_dir, dreams_path, hint_candidates=hint_candidates, fields=fields, debug=args.debug, dry_run=args.dry_run)

    if result:
        print("\n=== 做梦入口选择结果 ===")
        print(f"入口日志: {result['entry_path']}")
        print(f"选择理由: {result['reason']}")
        print(f"梦境计数: {result['dream_count']}")

        for key, value in result.items():
            if key.startswith('entry_') and key != 'entry_path':
                print(f"  {key[6:]}: {value}")
    else:
        print("未能选择入口日志")


if __name__ == '__main__':
    main()
