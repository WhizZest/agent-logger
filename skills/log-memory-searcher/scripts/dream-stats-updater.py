#!/usr/bin/env python3
"""
梦境统计更新器
从梦境报告中提取 path_visited，批量更新日志的 dream_visit_count 和 last_dreamed

使用方法:
    python dream-stats-updater.py --report <梦境报告路径>
    python dream-stats-updater.py --report <梦境报告路径> --log-base <日志根目录>
    python dream-stats-updater.py --report <梦境报告路径> --dry-run
"""

import argparse
import re
import subprocess
from pathlib import Path
from datetime import datetime

from _yaml_utils import extract_yaml_frontmatter


def detect_log_base(report_path):
    report = Path(report_path).resolve()
    for parent in report.parents:
        if parent.name == '.log':
            return str(parent)
    raise SystemExit(f'错误: 无法从报告路径中检测到 .log 目录: {report_path}')


def find_in_workspace(filename, search_root):
    """使用 fd 在 workspace 中搜索文件。

    注意: 仅按文件名搜索，如果存在多个同名文件，返回的是 fd 找到的第一个结果。
    这不影响判断正确性——预期路径下文件不存在即为非日志，无论 fd 找到哪个文件。
    本函数依赖外部工具 fd，未安装时降级返回 None（标记为 [未找到]）。

    Args:
        filename: 要搜索的文件名（仅文件名，不含路径）
        search_root: 搜索根目录

    Returns:
        str or None: 找到的第一个文件路径，未找到或 fd 不可用返回 None
    """
    try:
        result = subprocess.run(
            ['fd', '--hidden', '--no-ignore', '--max-results', '1',
             '--glob', filename, str(search_root)],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def update_log_stats(log_path, current_time, dry_run=False):
    """更新日志文件的 dream_visit_count 和 last_dreamed。

    仅操作 YAML frontmatter 区域（第一个 ---...---），正文不受影响。

    格式假设：
    - dream_visit_count 为纯数字值（如 dream_visit_count: 3）
    - last_dreamed 使用双引号包裹的 ISO 时间戳（如 last_dreamed: "2026-01-01T00:00:00+08:00"）
    - 新增字段时，last_dreamed 紧跟在 dream_visit_count 之后

    Returns:
        bool: 成功返回 True，失败返回 False
    """
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except (OSError, UnicodeDecodeError) as e:
        print(f'  [错误] 读取失败: {e}')
        return False

    fm_match = re.match(r'^(---\s*\n.*?\n---)', content, re.DOTALL)
    if not fm_match:
        print(f'  [错误] 未找到 frontmatter')
        return False

    frontmatter = fm_match.group(1)
    body = content[fm_match.end():]

    vc_match = re.search(r'dream_visit_count:\s*(\d+)', frontmatter)
    if vc_match:
        new_count = int(vc_match.group(1)) + 1
        frontmatter = re.sub(
            r'dream_visit_count:\s*\d+',
            f'dream_visit_count: {new_count}',
            frontmatter
        )
    else:
        frontmatter = re.sub(
            r'\n---',
            f'\ndream_visit_count: 1\n---',
            frontmatter,
            count=1
        )

    if 'last_dreamed:' in frontmatter:
        frontmatter = re.sub(
            r'last_dreamed:\s*"[^"]*"',
            f'last_dreamed: "{current_time}"',
            frontmatter
        )
    else:
        frontmatter = re.sub(
            r'(dream_visit_count:\s*\d+\n)',
            f'\\1last_dreamed: "{current_time}"\n',
            frontmatter
        )

    if dry_run:
        return True

    try:
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter + body)
        return True
    except (OSError, UnicodeEncodeError) as e:
        print(f'  [错误] 写入失败: {e}')
        return False


def main():
    parser = argparse.ArgumentParser(
        description='从梦境报告提取 path_visited，批量更新日志的 dream_visit_count 和 last_dreamed'
    )
    parser.add_argument(
        '--report', '-r',
        required=True,
        help='梦境报告文件路径'
    )
    parser.add_argument(
        '--log-base',
        default=None,
        help='日志根目录（默认从报告路径自动检测 .log 目录）'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='仅预览，不实际修改文件'
    )
    parser.add_argument(
        '--time',
        default=None,
        help='指定时间戳（默认使用系统本地时区）'
    )

    args = parser.parse_args()

    report_path = Path(args.report)
    if not report_path.exists():
        print(f'错误: 报告文件不存在: {report_path}')
        return 1

    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()

    metadata = extract_yaml_frontmatter(content)
    if not metadata:
        print(f'错误: 无法解析报告 frontmatter: {report_path}')
        return 1

    path_visited = metadata.get('path_visited')
    if not path_visited:
        print('错误: 报告中未找到 path_visited 字段')
        return 1

    log_base = Path(args.log_base) if args.log_base else Path(detect_log_base(report_path))

    if args.time:
        current_time = args.time
    else:
        local_now = datetime.now().astimezone()
        current_time = local_now.isoformat(timespec='seconds')

    print(f'日志根目录: {log_base}')
    print(f'时间戳: {current_time}')
    print(f'待更新日志数: {len(path_visited)}')
    if args.dry_run:
        print('模式: DRY RUN（不实际修改）')
    print()

    success = 0
    skipped = 0
    failed = 0

    resolved_base = log_base.resolve()

    for entry in path_visited:
        log_path = (log_base / entry).resolve()

        try:
            log_path.relative_to(resolved_base)
        except ValueError:
            print(f'  [拒绝] {entry} (路径不在日志目录内)')
            skipped += 1
            continue

        if not log_path.exists():
            filename = Path(entry).name
            # 仅按文件名搜索，多个同名文件时 fd 返回第一个匹配。
            # 无论匹配到哪个文件，[非日志] 的判断总是正确的——
            # 预期路径下文件不存在，即非需更新的日志。
            found = find_in_workspace(filename, log_base.parent)
            if found:
                print(f'  [非日志] {entry}')
            else:
                print(f'  [未找到] {entry}')
            skipped += 1
            continue

        if update_log_stats(str(log_path), current_time, dry_run=args.dry_run):
            print(f'  [OK] {entry}')
            success += 1
        else:
            print(f'  [失败] {entry}')
            failed += 1

    print()
    print(f'完成: {success} 个已更新, {skipped} 个跳过, {failed} 个失败')

    return 0


if __name__ == '__main__':
    exit(main())