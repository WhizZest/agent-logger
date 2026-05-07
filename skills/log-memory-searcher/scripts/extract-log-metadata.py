#!/usr/bin/env python3
"""
提取日志文件的元信息并生成索引文件
输出文件：metadata-index.md（默认）或 metadata-index.json

使用方法:
    python extract-log-metadata.py --path <目录路径>                          # 使用默认字段
    python extract-log-metadata.py -p <目录路径> --fields title,type         # 指定字段
    python extract-log-metadata.py -p <目录路径> --all                       # 提取所有字段
    python extract-log-metadata.py -p <目录路径> --search weread             # 搜索关键词
    python extract-log-metadata.py -p <目录路径> --recent-days 7             # 最近7天
    python extract-log-metadata.py -p <目录路径> --from-date 2026-04-01      # 日期范围
    python extract-log-metadata.py -p <目录路径> --format json               # JSON格式输出
"""

import os
import json
import re
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta, date

def extract_yaml_frontmatter(content):
    """提取 YAML front matter 中的所有字段"""
    # 匹配 --- ... --- 之间的内容
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return None
    
    yaml_content = match.group(1)
    metadata = {}
    
    # 动态提取所有 YAML 键值对
    # 匹配 pattern: key: value 或 key: "value" 或 key: 'value'
    # 也支持多行数组 tags: [...]
    lines = yaml_content.split('\n')
    current_key = None
    current_value = []
    in_array = False
    
    for line in lines:
        # 检查是否是新的键值对
        kv_match = re.match(r'^(\w+):\s*(.*)', line)
        
        if kv_match:
            # 如果之前有未完成的数组，保存它
            if current_key and in_array:
                # 解析数组内容
                array_str = '\n'.join(current_value)
                # 提取方括号内的内容
                array_match = re.search(r'\[(.*)\]', array_str, re.DOTALL)
                if array_match:
                    items_str = array_match.group(1)
                    items = [item.strip().strip('"').strip("'") for item in items_str.split(',') if item.strip()]
                    metadata[current_key] = items
            
            current_key = kv_match.group(1).strip()
            current_value = [kv_match.group(2).strip()]
            
            # 检查是否是数组开始
            if '[' in kv_match.group(2) and ']' not in kv_match.group(2):
                in_array = True
            elif '[' in kv_match.group(2) and ']' in kv_match.group(2):
                # 单行数组
                array_match = re.search(r'\[(.*)\]', kv_match.group(2))
                if array_match:
                    items_str = array_match.group(1)
                    items = [item.strip().strip('"').strip("'") for item in items_str.split(',') if item.strip()]
                    metadata[current_key] = items
                else:
                    # 简单的字符串值
                    value = kv_match.group(2).strip().strip('"').strip("'")
                    metadata[current_key] = value
                current_key = None
                in_array = False
            else:
                # 简单的字符串值
                value = kv_match.group(2).strip().strip('"').strip("'")
                metadata[current_key] = value
                current_key = None
                in_array = False
        elif in_array and current_key:
            # 继续收集数组内容
            current_value.append(line)
    
    # 处理最后一个未完成的数组
    if current_key and in_array:
        array_str = '\n'.join(current_value)
        array_match = re.search(r'\[(.*)\]', array_str, re.DOTALL)
        if array_match:
            items_str = array_match.group(1)
            items = [item.strip().strip('"').strip("'") for item in items_str.split(',') if item.strip()]
            metadata[current_key] = items
    
    return metadata

def filter_metadata(metadata, fields=None, show_all=False):
    """根据指定的字段过滤元数据，默认字段始终包含。
    返回 (filtered_dict, found_user_fields_set)"""
    if show_all:
        return metadata, set()

    default_fields = ['title', 'description', 'file_path']
    user_fields = []

    if not fields:
        fields = default_fields
    else:
        user_fields = [f for f in fields if f not in default_fields]
        fields = list(dict.fromkeys(default_fields + fields))

    filtered = {}
    found_user = set()
    for field in fields:
        if field in metadata:
            filtered[field] = metadata[field]
            if field in user_fields:
                found_user.add(field)

    return filtered, found_user

def parse_search_terms(search_terms):
    """
    解析搜索参数，将每个 search term 按 | 分割成 OR 组
    
    Args:
        search_terms: 搜索词列表，例如 ['weread|微信读书', 'debug']
    
    Returns:
        关键词组列表，例如 [['weread', '微信读书'], ['debug']]
    """
    if not search_terms:
        return []
    
    keyword_groups = []
    for term in search_terms:
        # 按 | 分割，得到 OR 组
        # 注意：不支持转义，如果关键词以 | 开头或结尾会被当作普通字符
        if '|' in term and not term.startswith('|') and not term.endswith('|'):
            keywords = [k.strip() for k in term.split('|') if k.strip()]
            if keywords:
                keyword_groups.append(keywords)
        else:
            # 没有 | 或者 | 在开头/结尾，当作单个关键词
            keyword_groups.append([term])
    
    return keyword_groups

def match_keywords(metadata, keyword_groups):
    """
    检查元数据是否匹配关键词
    
    Args:
        metadata: 元数据字典
        keyword_groups: 关键词组列表，每组内部是 OR 逻辑，组之间是 AND 逻辑
                       例如: [['weread', '微信读书'], ['debug', 'test']]
                       表示: (weread OR 微信读书) AND (debug OR test)
    
    Returns:
        bool: 是否匹配
    """
    if not keyword_groups:
        return True
    
    # 将所有文本字段转换为小写用于搜索
    text_content = []
    
    # 检查 title
    if 'title' in metadata and metadata['title']:
        text_content.append(str(metadata['title']).lower())
    
    # 检查 description
    if 'description' in metadata and metadata['description']:
        text_content.append(str(metadata['description']).lower())
    
    # 检查 tags（数组）
    if 'tags' in metadata and isinstance(metadata['tags'], list):
        for tag in metadata['tags']:
            text_content.append(str(tag).lower())
    
    # 检查 type
    if 'type' in metadata and metadata['type']:
        text_content.append(str(metadata['type']).lower())
    
    # 检查 error_pattern
    if 'error_pattern' in metadata and metadata['error_pattern']:
        text_content.append(str(metadata['error_pattern']).lower())
    
    # 合并所有文本内容
    full_text = ' '.join(text_content)
    
    # 检查所有关键词组（组之间是 AND 逻辑）
    for group in keyword_groups:
        # 组内是 OR 逻辑，只要有一个关键词匹配即可
        group_matched = False
        for keyword in group:
            keyword_lower = keyword.lower()
            if keyword_lower in full_text:
                group_matched = True
                break
        
        # 如果这一组没有匹配，则整体不匹配
        if not group_matched:
            return False
    
    return True

def parse_datetime(time_str):
    """
    解析 ISO 8601 时间字符串为 datetime 对象
    
    Args:
        time_str: ISO 8601 格式的时间字符串
    
    Returns:
        datetime 对象，如果解析失败返回 None
    """
    if not time_str:
        return None
    try:
        dt = datetime.fromisoformat(time_str)
        # 如果没有时区信息，假设为 UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError, AttributeError):
        return None

def get_sort_key(metadata):
    """
    获取排序键值（datetime 对象）
    
    优先级：last_accessed > created > 最小日期
    """
    # 优先使用 last_accessed
    if 'last_accessed' in metadata and metadata['last_accessed']:
        dt = parse_datetime(metadata['last_accessed'])
        if dt is not None:
            return dt
    
    # 否则使用 created
    if 'created' in metadata and metadata['created']:
        dt = parse_datetime(metadata['created'])
        if dt is not None:
            return dt
    
    # 都没有，放到最后（使用最小日期）
    return datetime.min.replace(tzinfo=timezone.utc)

def check_date_range(metadata, from_date=None, to_date=None, recent_days=None):
    """
    检查元数据是否在指定的时间范围内
    
    Args:
        metadata: 元数据字典
        from_date: 起始日期（date 对象），None 表示不限制
        to_date: 结束日期（date 对象），None 表示不限制
        recent_days: 最近 N 天，None 表示不使用此限制
    
    Returns:
        bool: 是否在时间范围内
    """
    # 如果没有设置任何时间限制，返回 True
    if from_date is None and to_date is None and recent_days is None:
        return True
    
    # 获取元数据的时间（优先 last_accessed，否则 created）
    dt = None
    if 'last_accessed' in metadata and metadata['last_accessed']:
        dt = parse_datetime(metadata['last_accessed'])
    
    if dt is None and 'created' in metadata and metadata['created']:
        dt = parse_datetime(metadata['created'])
    
    # 如果没有时间信息，排除
    if dt is None:
        return False
    
    # 转换为本地时区的日期
    local_dt = dt.astimezone()
    local_date = local_dt.date()
    
    # 检查 recent_days
    if recent_days is not None and recent_days > 0:
        today = date.today()
        cutoff_date = today - timedelta(days=recent_days - 1)  # 包含今天
        if local_date < cutoff_date:
            return False
    
    # 检查 from_date
    if from_date is not None:
        if local_date < from_date:
            return False
    
    # 检查 to_date
    if to_date is not None:
        if local_date > to_date:
            return False
    
    return True

def format_yaml_value(value):
    """
    格式化 YAML 值
    
    Args:
        value: 要格式化的值
    
    Returns:
        str: 格式化后的 YAML 字符串
    """
    if isinstance(value, list):
        # 列表格式化为 YAML 数组
        items = []
        for item in value:
            if isinstance(item, str):
                items.append(f'"{item}"')
            else:
                items.append(str(item))
        return '[' + ', '.join(items) + ']'
    elif isinstance(value, str):
        # 字符串需要加引号
        return f'"{value}"'
    else:
        # 其他类型直接转换
        return str(value)

def save_as_md(metadata_list, output_file):
    """
    将元数据保存为 Markdown 格式
    
    Args:
        metadata_list: 元数据列表
        output_file: 输出文件路径
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, metadata in enumerate(metadata_list):
            # 如果不是第一个，先写入分隔符
            if i > 0:
                f.write('---\n')
            
            # 写入所有字段
            for key, value in metadata.items():
                formatted_value = format_yaml_value(value)
                f.write(f'{key}: {formatted_value}\n')
        
        # 最后添加一个 ---
        if metadata_list:
            f.write('---\n')

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='提取日志文件的元信息')
    parser.add_argument('--fields', '-f', nargs='+', 
                       help='要提取的字段列表，逗号或空格分隔，例如: --fields title,type,tags')
    parser.add_argument('--all', '-a', action='store_true',
                       help='提取所有字段')
    parser.add_argument('--search', '-s', nargs='+',
                       help='搜索关键词，支持多个关键词（AND 逻辑），用 | 分隔表示 OR 逻辑')
    parser.add_argument('--oldest-first', action='store_true',
                       help='按时间从旧到新排序（默认是从新到旧）')
    parser.add_argument('--limit', '-l', type=int, default=50,
                       help='限制输出数量（默认 50）')
    parser.add_argument('--recent-days', '-r', type=int,
                       help='限制最近 N 天的结果')
    parser.add_argument('--from-date', dest='from_date', type=str,
                       help='起始日期（YYYY-MM-DD）')
    parser.add_argument('--to-date', dest='to_date', type=str,
                       help='结束日期（YYYY-MM-DD）')
    parser.add_argument('--format', choices=['md', 'json'], default='md',
                       help='输出格式：md（默认）或 json')
    parser.add_argument('--path', '-p', type=str, required=True,
                       help='指定扫描的日志目录路径（必需）')
    parser.add_argument('--debug', '-d', action='store_true',
                       help='显示详细的处理过程')
    args = parser.parse_args()
    
    if args.fields:
        flat_fields = []
        for f in args.fields:
            flat_fields.extend([x.strip() for x in f.split(',') if x.strip()])
        args.fields = flat_fields
    
    # 验证和解析日期参数
    from_date_obj = None
    to_date_obj = None
    
    if args.from_date:
        try:
            from_date_obj = datetime.strptime(args.from_date, '%Y-%m-%d').date()
        except ValueError:
            print(f"错误: 起始日期格式不正确，应为 YYYY-MM-DD，收到: {args.from_date}")
            return
    
    if args.to_date:
        try:
            to_date_obj = datetime.strptime(args.to_date, '%Y-%m-%d').date()
        except ValueError:
            print(f"错误: 结束日期格式不正确，应为 YYYY-MM-DD，收到: {args.to_date}")
            return
    
    # 验证日期范围
    if from_date_obj and to_date_obj and from_date_obj > to_date_obj:
        print(f"错误: 起始日期 ({from_date_obj}) 不能晚于结束日期 ({to_date_obj})")
        return
    
    # 获取脚本所在目录
    script_dir = Path(__file__).parent
    
    # 确定日志目录（必须指定路径）
    log_dir = Path(args.path)
    if not log_dir.is_absolute():
        # 如果是相对路径，相对于当前工作目录
        log_dir = Path.cwd() / log_dir
    
    # 根据格式确定输出文件名
    if args.format == 'md':
        output_file = log_dir / 'metadata-index.md'
    else:
        output_file = log_dir / 'metadata-index.json'
    
    if not log_dir.exists():
        print(f"错误: 日志目录不存在: {log_dir}")
        return
    
    # 获取所有 .md 文件
    md_files = sorted(log_dir.rglob('*.md'))
    
    # 排除 dreams/ 目录下的文件
    dreams_dir = log_dir / 'dreams'
    if dreams_dir.exists():
        dreams_files = set(dreams_dir.rglob('*.md'))
        md_files = [f for f in md_files if f not in dreams_files]
    
    print("开始提取元信息...")
    print(f"找到 {len(md_files)} 个日志文件")
    
    metadata_list = []
    found_user_fields = set()
    
    for file_path in md_files:
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取 YAML front matter
            metadata = extract_yaml_frontmatter(content)
            
            if metadata:
                # 添加文件路径信息（相对于日志目录）
                rel_path = file_path.relative_to(log_dir)
                metadata['file_path'] = str(rel_path).replace('\\', '/')
                
                # 检查时间范围
                if not check_date_range(metadata, from_date_obj, to_date_obj, args.recent_days):
                    if args.debug:
                        print(f"  [SKIP] {file_path.name} - 不在时间范围内")
                    continue
                
                # 如果指定了搜索关键词，先进行筛选
                if args.search:
                    keyword_groups = parse_search_terms(args.search)
                    if not match_keywords(metadata, keyword_groups):
                        if args.debug:
                            print(f"  [SKIP] {file_path.name} - 不匹配关键词")
                        continue
                
                # 根据参数过滤字段
                filtered_metadata, found = filter_metadata(metadata, args.fields, args.all)
                found_user_fields.update(found)
                
                metadata_list.append(filtered_metadata)
                if args.debug:
                    print(f"  [OK] {file_path.name}")
            else:
                if args.debug:
                    print(f"  [WARN] {file_path.name} - 没有 YAML front matter")
        
        except Exception as e:
            print(f"  [ERROR] {file_path.name} - 错误: {str(e)}")
    
    # 排序：根据时间字段（不受 --fields 影响，基于完整元数据）
    reverse_order = not args.oldest_first  # 默认从新到旧
    metadata_list.sort(key=get_sort_key, reverse=reverse_order)
    
    # 限制数量
    total_count = len(metadata_list)
    if args.limit and total_count > args.limit:
        metadata_list = metadata_list[:args.limit]
        print(f"\n注意：共有 {total_count} 个结果，已限制为前 {args.limit} 个")
    
    # 保存为指定格式
    if args.format == 'md':
        save_as_md(metadata_list, output_file)
    else:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metadata_list, f, ensure_ascii=False, indent=2)
    
    print(f"\n完成！")
    print(f"已提取 {len(metadata_list)} 个文件的元信息")
    print(f"输出文件: {output_file}")

    if args.fields and not args.all:
        default_fields = {'title', 'description', 'file_path'}
        user_fields = set(args.fields) - default_fields
        missing = user_fields - found_user_fields
        if missing:
            print(f"\n警告: 以下字段在所有文件中均不存在: {', '.join(sorted(missing))}")

    # 显示统计信息（只在提取了对应字段时显示）
    if metadata_list:
        # 检查是否提取了 type 字段
        has_type = any('type' in meta for meta in metadata_list)
        if has_type or args.all:
            type_stats = {}
            for meta in metadata_list:
                t = meta.get('type', 'unknown')
                type_stats[t] = type_stats.get(t, 0) + 1
            
            print("\n按类型统计:")
            for t, count in sorted(type_stats.items(), key=lambda x: x[1], reverse=True):
                print(f"  {t}: {count}")
        
        # 检查是否提取了 language 字段
        has_language = any('language' in meta for meta in metadata_list)
        if has_language or args.all:
            lang_stats = {}
            for meta in metadata_list:
                lang = meta.get('language', 'unknown')
                lang_stats[lang] = lang_stats.get(lang, 0) + 1
            
            print("\n按语言统计:")
            for lang, count in sorted(lang_stats.items(), key=lambda x: x[1], reverse=True):
                print(f"  {lang}: {count}")

if __name__ == '__main__':
    main()
