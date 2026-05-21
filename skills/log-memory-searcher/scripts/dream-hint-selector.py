#!/usr/bin/env python3
"""
入梦提示选择器
从 dream-hints.yaml 中选择一个提示（或"无提示"），更新提示状态

使用方法:
    python dream-hint-selector.py --dreams-path <workspace>/.log/dreams/
    python dream-hint-selector.py --dreams-path <workspace>/.log/dreams/ --debug
    python dream-hint-selector.py --dreams-path <workspace>/.log/dreams/ --dry-run
"""

import argparse
import random
from pathlib import Path
from datetime import datetime

try:
    import yaml
except ImportError:
    yaml = None


NO_HINT_PROBABILITY = 0.3


def _parse_yaml_simple(content):
    hints = []
    lines = content.split('\n')
    i = 0
    in_hints = False

    while i < len(lines):
        line = lines[i]

        if line.strip() == 'hints:':
            in_hints = True
            i += 1
            continue

        if not in_hints:
            i += 1
            continue

        if not line.startswith('  - ') and line.strip() and not line.startswith(' '):
            break

        if line.strip().startswith('- ') and ':' in line:
            hint = {}
            first_key = line.strip()[2:].split(':', 1)[0].strip()
            first_val = line.strip()[2:].split(':', 1)[1].strip().strip('"').strip("'")
            hint[first_key] = first_val
            i += 1
            while i < len(lines):
                sub = lines[i]
                if (sub.strip().startswith('- ') and ':' in sub) or (sub and not sub.startswith('    ') and sub.strip()):
                    break
                if ':' in sub:
                    key = sub.strip().split(':', 1)[0].strip()
                    if key == 'description':
                        i += 1
                        continue
                    val = sub.strip().split(':', 1)[1].strip().strip('"').strip("'")
                    if key == 'cooldown_days':
                        try:
                            val = int(val)
                        except ValueError:
                            val = 0
                    elif key == 'priority':
                        try:
                            val = int(val)
                        except ValueError:
                            val = 1
                    elif key == 'disposable':
                        val = val.lower() in ('true', 'yes', '1')
                    elif key == 'cooldown_start':
                        if val in ('null', 'None', ''):
                            val = None
                    elif key == 'associated_reports':
                        val = []
                        i += 1
                        while i < len(lines):
                            item_line = lines[i]
                            stripped = item_line.strip()
                            if stripped.startswith('- ') and not item_line.startswith('  - '):
                                item_val = stripped[2:].strip().strip('"').strip("'")
                                val.append(item_val)
                                i += 1
                            elif stripped and not stripped.startswith('#'):
                                break
                            else:
                                i += 1
                        hint[key] = val
                        continue
                    hint[key] = val
                i += 1
            if 'description' in hint:
                hints.append(hint)
        else:
            i += 1

    return hints


def load_hints(hints_path):
    if not hints_path.exists():
        return None

    try:
        with open(hints_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return None

    if yaml:
        try:
            data = yaml.safe_load(content)
            if isinstance(data, dict) and 'hints' in data:
                return data['hints']
        except Exception:
            pass

    return _parse_yaml_simple(content)


def _normalize_cooldown_start(hints):
    for hint in hints:
        cooldown_start = hint.get('cooldown_start')
        if not cooldown_start:
            continue
        dt = _parse_iso_datetime(cooldown_start)
        if dt is None:
            continue
        if dt.tzinfo is None:
            dt = dt.astimezone()
        normalized = dt.isoformat(timespec='seconds')
        if hint['cooldown_start'] != normalized:
            hint['cooldown_start'] = normalized


def save_hints(hints_path, hints):
    hints_path.parent.mkdir(parents=True, exist_ok=True)

    lines = ['hints:']
    for hint in hints:
        desc = hint.get('description', '').replace('"', '\\"')
        lines.append(f'  - description: "{desc}"')
        lines.append(f'    type: {hint.get("type", "perspective")}')
        lines.append(f'    cooldown_days: {hint.get("cooldown_days", 0)}')
        lines.append(f'    priority: {hint.get("priority", 1)}')
        cooldown_start = hint.get('cooldown_start')
        if cooldown_start:
            lines.append(f'    cooldown_start: "{cooldown_start}"')
        else:
            lines.append(f'    cooldown_start: null')
        if hint.get('disposable'):
            lines.append(f'    disposable: true')
        associated = hint.get('associated_reports')
        if associated:
            lines.append(f'    associated_reports:')
            for report in associated:
                lines.append(f'      - "{report}"')

    with open(hints_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def _parse_iso_datetime(s):
    if s is None:
        return None
    if isinstance(s, datetime):
        return s
    if not isinstance(s, str) or s in ('null', 'None', ''):
        return None
    s = s.replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def compute_weight(hint, now):
    priority = hint.get('priority', 1)
    cooldown_days = hint.get('cooldown_days', 0)
    cooldown_start = hint.get('cooldown_start')

    if cooldown_days == 0:
        return float(priority)

    if cooldown_start is None:
        days_since_cooldown = float(cooldown_days)
        return priority * (1 + days_since_cooldown / cooldown_days)

    start_dt = _parse_iso_datetime(cooldown_start)
    if start_dt is None:
        return float(priority)

    if start_dt.tzinfo is None:
        start_dt = start_dt.astimezone()

    elapsed_days = (now - start_dt).total_seconds() / 86400.0
    days_since_cooldown = max(0, elapsed_days - cooldown_days)

    return priority * (1 + days_since_cooldown / cooldown_days)


def is_in_cooldown(hint, now):
    cooldown_days = hint.get('cooldown_days', 0)
    cooldown_start = hint.get('cooldown_start')

    if cooldown_days == 0:
        return False

    if cooldown_start is None:
        return False

    start_dt = _parse_iso_datetime(cooldown_start)
    if start_dt is None:
        return False

    if start_dt.tzinfo is None:
        start_dt = start_dt.astimezone()

    elapsed_days = (now - start_dt).total_seconds() / 86400.0
    return elapsed_days < cooldown_days


def select_hint(dreams_path, debug=False, dry_run=False):
    hints_path = dreams_path / 'dream-hints.yaml'
    hints = load_hints(hints_path)

    if hints is None or len(hints) == 0:
        if debug:
            if hints is None:
                print("[DEBUG] dream-hints.yaml 不存在或无法解析")
            else:
                print("[DEBUG] dream-hints.yaml 为空")
        return {'selected': None}

    now = datetime.now().astimezone()

    available = []
    for hint in hints:
        if not is_in_cooldown(hint, now):
            available.append(hint)
        elif debug:
            print(f"[DEBUG] 冷却中: {hint.get('description')} (cooldown_days={hint.get('cooldown_days')}, cooldown_start={hint.get('cooldown_start')})")

    if debug:
        print(f"[DEBUG] 可用提示数: {len(available)} / {len(hints)}")

    if len(available) == 0:
        if debug:
            print("[DEBUG] 所有提示都在冷却期，选择无提示")
        return {'selected': None}

    if random.random() < NO_HINT_PROBABILITY:
        if debug:
            print(f"[DEBUG] 无提示（固定概率 {NO_HINT_PROBABILITY*100:.0f}%）")
        if dry_run:
            print("[DRY-RUN] 不会实际保存改动")
        return {'selected': None}

    candidates = []
    weights = []

    for hint in available:
        w = compute_weight(hint, now)
        candidates.append(hint)
        weights.append(w)
        if debug:
            print(f"[DEBUG] 提示 {hint.get('description')}: weight={w:.2f} (priority={hint.get('priority')}, cooldown_days={hint.get('cooldown_days')}, cooldown_start={hint.get('cooldown_start')})")

    total = sum(weights)
    r = random.uniform(0, total)
    cumulative = 0
    selected = candidates[-1]

    for candidate, weight in zip(candidates, weights):
        cumulative += weight
        if r <= cumulative:
            selected = candidate
            break

    if selected is None:
        if debug:
            print("[DEBUG] 选中：无提示")
        return {'selected': None}

    is_disposable = selected.get('disposable', False)

    if dry_run:
        if debug:
            if is_disposable:
                print(f"[DEBUG] [DRY-RUN] 如果实际运行，将删除一次性提示: {selected.get('description')}")
            else:
                print(f"[DEBUG] [DRY-RUN] 如果实际运行，将更新 cooldown_start")
        print("[DRY-RUN] 不会实际保存改动")
        return {
            'selected': selected,
            'dry_run': True,
            'would_delete': is_disposable,
            'would_update_cooldown': not is_disposable,
        }

    selected['cooldown_start'] = now.isoformat(timespec='seconds')

    if is_disposable:
        hints = [h for h in hints if h.get('description') != selected['description']]
        if debug:
            print(f"[DEBUG] 已删除一次性提示: {selected.get('description')}")

    _normalize_cooldown_start(hints)
    save_hints(hints_path, hints)

    return {'selected': selected}


def main():
    parser = argparse.ArgumentParser(description='入梦提示选择器')
    parser.add_argument('--dreams-path', type=str, required=True,
                        help='梦境目录路径（必需）')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='显示详细调试信息')
    parser.add_argument('--dry-run', action='store_true',
                        help='仅预览选择结果，不修改文件')
    args = parser.parse_args()

    dreams_path = Path(args.dreams_path)
    if not dreams_path.is_absolute():
        dreams_path = Path.cwd() / dreams_path

    dreams_path.mkdir(parents=True, exist_ok=True)

    result = select_hint(dreams_path, debug=args.debug, dry_run=args.dry_run)

    print("\n=== 入梦提示选择结果 ===")
    if args.dry_run:
        print("[DRY-RUN 模式] 以下为预览，未做任何实际改动")
    selected = result.get('selected')
    if selected is None:
        print("无提示：自由联想")
    else:
        print(f"描述: {selected.get('description')}")
        print(f"类型: {selected.get('type')}")
        if result.get('would_delete'):
            print("一次性: 是（如果实际运行将从提示集中删除）")
        elif result.get('would_update_cooldown'):
            print("状态: 如果实际运行将记录冷却起始时间")
        elif selected.get('disposable'):
            print("一次性: 是（已从提示集中删除）")
        associated = selected.get('associated_reports')
        if associated:
            print(f"关联报告: {', '.join(associated)}")


if __name__ == '__main__':
    main()
