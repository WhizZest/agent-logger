"""
YAML frontmatter 解析工具
支持简单键值对、bracket 数组 ([...])、dash 列表 (- ...)
"""

import re


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
        kv_match = re.match(r'^(\w+):\s*(.*)', line)
        dash_match = re.match(r'^\s+-\s+(.*)', line)

        if kv_match:
            if current_key and in_bracket_array:
                array_str = '\n'.join(current_value)
                array_match = re.search(r'\[(.*)\]', array_str, re.DOTALL)
                if array_match:
                    items_str = array_match.group(1)
                    items = [item.strip().strip('"').strip("'") for item in items_str.split(',') if item.strip()]
                    metadata[current_key] = items
                in_bracket_array = False
            elif current_key and in_dash_list:
                metadata[current_key] = current_value
                in_dash_list = False
            elif current_key and not in_bracket_array and not in_dash_list:
                if len(current_value) == 1:
                    metadata[current_key] = current_value[0]
                else:
                    metadata[current_key] = '\n'.join(current_value)

            current_key = kv_match.group(1).strip()
            value_part = kv_match.group(2).strip()
            current_value = [value_part]
            in_bracket_array = False
            in_dash_list = False

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

    if current_key and in_bracket_array:
        array_str = '\n'.join(current_value)
        array_match = re.search(r'\[(.*)\]', array_str, re.DOTALL)
        if array_match:
            items_str = array_match.group(1)
            items = [item.strip().strip('"').strip("'") for item in items_str.split(',') if item.strip()]
            metadata[current_key] = items
    elif current_key and in_dash_list:
        metadata[current_key] = current_value
    elif current_key and not in_bracket_array and not in_dash_list:
        if len(current_value) == 1:
            metadata[current_key] = current_value[0]
        else:
            metadata[current_key] = '\n'.join(current_value)

    return metadata