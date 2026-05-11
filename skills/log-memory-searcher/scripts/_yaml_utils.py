"""
YAML frontmatter 解析工具
支持简单键值对、bracket 数组 ([...])、dash 列表 (- ...)

限制：bracket 数组使用 split(',') 解析，不处理引号内的逗号。
      例如 ["tag1, with comma", "tag2"] 会被错误拆分为三项。
"""

import re


def _finalize_key(metadata, current_key, current_value, in_bracket_array, in_dash_list):
    if in_bracket_array:
        array_str = '\n'.join(current_value)
        array_match = re.search(r'\[(.*)\]', array_str, re.DOTALL)
        if array_match:
            items_str = array_match.group(1)
            items = [item.strip().strip('"').strip("'") for item in items_str.split(',') if item.strip()]
            metadata[current_key] = items
    elif in_dash_list:
        metadata[current_key] = current_value
    else:
        if len(current_value) == 1:
            metadata[current_key] = current_value[0]
        else:
            metadata[current_key] = '\n'.join(current_value)


def extract_yaml_frontmatter(content):
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return None

    yaml_content = match.group(1)
    metadata = {}

    lines = yaml_content.split('\n')
    current_key = None
    current_value = []
    in_bracket_array = False
    in_dash_list = False

    for line in lines:
        kv_match = re.match(r'^([\w-]+):\s*(.*)', line)
        dash_match = re.match(r'^\s+-\s+(.*)', line)

        if kv_match:
            if current_key:
                _finalize_key(metadata, current_key, current_value, in_bracket_array, in_dash_list)
                in_bracket_array = False
                in_dash_list = False

            current_key = kv_match.group(1).strip()
            value_part = kv_match.group(2).strip()
            current_value = [value_part]

            if '[' in value_part and ']' not in value_part:
                in_bracket_array = True
            elif '[' in value_part and ']' in value_part:
                array_match = re.search(r'\[(.*)\]', value_part)
                if array_match:
                    items_str = array_match.group(1)
                    items = [item.strip().strip('"').strip("'") for item in items_str.split(',') if item.strip()]
                    metadata[current_key] = items
                else:
                    metadata[current_key] = value_part.strip('"').strip("'")
                current_key = None
            elif value_part == '':
                pass
            else:
                metadata[current_key] = value_part.strip('"').strip("'")
                current_key = None

        elif dash_match and current_key:
            if not in_dash_list:
                in_dash_list = True
                current_value = []
            item_value = dash_match.group(1).strip().strip('"').strip("'")
            current_value.append(item_value)

        elif in_bracket_array and current_key:
            current_value.append(line)

    if current_key:
        _finalize_key(metadata, current_key, current_value, in_bracket_array, in_dash_list)

    return metadata