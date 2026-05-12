import sys
import os
import subprocess
import importlib
import tempfile
import json
import math
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'skills' / 'log-memory-searcher' / 'scripts'))

from _yaml_utils import extract_yaml_frontmatter

dream_stats_updater = importlib.import_module('dream-stats-updater')
update_log_stats = dream_stats_updater.update_log_stats
find_in_workspace = dream_stats_updater.find_in_workspace

extract_log_metadata = importlib.import_module('extract-log-metadata')
CompactArrayEncoder = extract_log_metadata.CompactArrayEncoder


class TestExtractYamlFrontmatter:

    def test_simple_key_value(self):
        content = '---\ntype: log\ntitle: hello\n---'
        result = extract_yaml_frontmatter(content)
        assert result == {'type': 'log', 'title': 'hello'}

    def test_quoted_value(self):
        content = '---\ntitle: "hello world"\nauthor: \'someone\'\n---'
        result = extract_yaml_frontmatter(content)
        assert result == {'title': 'hello world', 'author': 'someone'}

    def test_empty_value(self):
        content = '---\ntype: log\ntitle:\n---'
        result = extract_yaml_frontmatter(content)
        assert result == {'type': 'log', 'title': ''}

    def test_empty_value_followed_by_dash_list(self):
        content = '---\ntype: dream\npath_visited:\n  - "a.md"\n  - "b.md"\n---'
        result = extract_yaml_frontmatter(content)
        assert result == {'type': 'dream', 'path_visited': ['a.md', 'b.md']}

    def test_single_line_bracket_array(self):
        content = '---\ntype: log\ntags: [a, b, c]\n---'
        result = extract_yaml_frontmatter(content)
        assert result == {'type': 'log', 'tags': ['a', 'b', 'c']}

    def test_multiline_bracket_array(self):
        content = '---\ntype: log\ntags: [\n  a,\n  b\n]\n---'
        result = extract_yaml_frontmatter(content)
        assert result == {'type': 'log', 'tags': ['a', 'b']}

    def test_dash_list(self):
        content = '---\ntype: dream\npath_visited:\n  - "a.md"\n  - "b.md"\n---'
        result = extract_yaml_frontmatter(content)
        assert result == {'type': 'dream', 'path_visited': ['a.md', 'b.md']}

    def test_mixed_bracket_and_dash(self):
        content = '---\ntype: log\ntags: [x, y]\nitems:\n  - "one"\n  - "two"\n---'
        result = extract_yaml_frontmatter(content)
        assert result == {'type': 'log', 'tags': ['x', 'y'], 'items': ['one', 'two']}

    def test_no_frontmatter(self):
        content = '# just a markdown file\n\nno frontmatter here'
        result = extract_yaml_frontmatter(content)
        assert result is None

    def test_empty_frontmatter(self):
        content = '---\n---\nbody'
        result = extract_yaml_frontmatter(content)
        assert result is None

    def test_multiple_keys(self):
        content = '---\ntype: log\ntitle: test\ncreated: "2026-01-01"\ntags: [a]\n---'
        result = extract_yaml_frontmatter(content)
        assert result == {
            'type': 'log',
            'title': 'test',
            'created': '2026-01-01',
            'tags': ['a'],
        }

    def test_hyphenated_key(self):
        content = '---\ntype: log\nlast-dreamed: "2026-01-01"\nvisit-count: 5\n---'
        result = extract_yaml_frontmatter(content)
        assert result == {
            'type': 'log',
            'last-dreamed': '2026-01-01',
            'visit-count': '5',
        }


class TestUpdateLogStats:

    def _make_log(self, frontmatter):
        return f'{frontmatter}\n\n# Body content\n\nSome text here.\n'

    def _read_log(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_both_fields_exist(self):
        fm = '---\ntitle: test\ndream_visit_count: 3\nlast_dreamed: "2026-01-01T00:00:00+08:00"\n---'
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', delete=False, encoding='utf-8'
        ) as f:
            f.write(self._make_log(fm))
            tmp_path = f.name

        try:
            result = update_log_stats(tmp_path, '2026-05-12T12:00:00+08:00')
            assert result is True

            content = self._read_log(tmp_path)
            assert 'dream_visit_count: 4' in content
            assert 'last_dreamed: "2026-05-12T12:00:00+08:00"' in content
            assert '# Body content' in content
        finally:
            os.unlink(tmp_path)

    def test_last_dreamed_single_quote(self):
        """单引号格式不被正则匹配，保持原样（符合 docstring 格式假设）"""
        fm = "---\ntitle: test\ndream_visit_count: 1\nlast_dreamed: '2026-01-01T00:00:00+08:00'\n---"
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', delete=False, encoding='utf-8'
        ) as f:
            f.write(self._make_log(fm))
            tmp_path = f.name

        try:
            result = update_log_stats(tmp_path, '2026-05-12T12:00:00+08:00')
            assert result is True

            content = self._read_log(tmp_path)
            assert 'dream_visit_count: 2' in content
            assert "last_dreamed: '2026-01-01T00:00:00+08:00'" in content
        finally:
            os.unlink(tmp_path)

    def test_last_dreamed_no_quote(self):
        """无引号格式不被正则匹配，保持原样（符合 docstring 格式假设）"""
        fm = '---\ntitle: test\ndream_visit_count: 1\nlast_dreamed: 2026-01-01T00:00:00+08:00\n---'
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', delete=False, encoding='utf-8'
        ) as f:
            f.write(self._make_log(fm))
            tmp_path = f.name

        try:
            result = update_log_stats(tmp_path, '2026-05-12T12:00:00+08:00')
            assert result is True

            content = self._read_log(tmp_path)
            assert 'dream_visit_count: 2' in content
            assert 'last_dreamed: 2026-01-01T00:00:00+08:00' in content
        finally:
            os.unlink(tmp_path)

    def test_only_visit_count_exists(self):
        fm = '---\ntitle: test\ndream_visit_count: 1\n---'
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', delete=False, encoding='utf-8'
        ) as f:
            f.write(self._make_log(fm))
            tmp_path = f.name

        try:
            result = update_log_stats(tmp_path, '2026-05-12T12:00:00+08:00')
            assert result is True

            content = self._read_log(tmp_path)
            assert 'dream_visit_count: 2' in content
            assert 'last_dreamed: "2026-05-12T12:00:00+08:00"' in content
            assert '# Body content' in content
        finally:
            os.unlink(tmp_path)

    def test_only_last_dreamed_exists(self):
        fm = '---\ntitle: test\nlast_dreamed: "2026-01-01T00:00:00+08:00"\n---'
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', delete=False, encoding='utf-8'
        ) as f:
            f.write(self._make_log(fm))
            tmp_path = f.name

        try:
            result = update_log_stats(tmp_path, '2026-05-12T12:00:00+08:00')
            assert result is True

            content = self._read_log(tmp_path)
            assert 'dream_visit_count: 1' in content
            assert 'last_dreamed: "2026-05-12T12:00:00+08:00"' in content
            assert '# Body content' in content
        finally:
            os.unlink(tmp_path)

    def test_neither_field_exists(self):
        fm = '---\ntitle: test\ntype: log\n---'
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', delete=False, encoding='utf-8'
        ) as f:
            f.write(self._make_log(fm))
            tmp_path = f.name

        try:
            result = update_log_stats(tmp_path, '2026-05-12T12:00:00+08:00')
            assert result is True

            content = self._read_log(tmp_path)
            assert 'dream_visit_count: 1' in content
            assert 'last_dreamed: "2026-05-12T12:00:00+08:00"' in content
            assert '# Body content' in content
        finally:
            os.unlink(tmp_path)

    def test_dry_run_does_not_modify(self):
        fm = '---\ntitle: test\ndream_visit_count: 5\nlast_dreamed: "2026-01-01T00:00:00+08:00"\n---'
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', delete=False, encoding='utf-8'
        ) as f:
            f.write(self._make_log(fm))
            tmp_path = f.name

        try:
            result = update_log_stats(tmp_path, '2026-05-12T12:00:00+08:00', dry_run=True)
            assert result is True

            content = self._read_log(tmp_path)
            assert 'dream_visit_count: 5' in content
            assert 'last_dreamed: "2026-01-01T00:00:00+08:00"' in content
        finally:
            os.unlink(tmp_path)

    def test_body_not_modified(self):
        fm = '---\ntitle: test\ndream_visit_count: 1\n---'
        body_with_similar = (
            '\n\n# dream_visit_count in body\n\n'
            'This body contains the text dream_visit_count: 999\n'
            'and last_dreamed: "should-not-change"\n'
        )
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', delete=False, encoding='utf-8'
        ) as f:
            f.write(fm + body_with_similar)
            tmp_path = f.name

        try:
            result = update_log_stats(tmp_path, '2026-05-12T12:00:00+08:00')
            assert result is True

            content = self._read_log(tmp_path)
            assert 'dream_visit_count: 2' in content
            assert 'dream_visit_count: 999' in content
            assert 'last_dreamed: "should-not-change"' in content
        finally:
            os.unlink(tmp_path)

    def test_no_frontmatter(self):
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', delete=False, encoding='utf-8'
        ) as f:
            f.write('# No frontmatter\n\nJust body.')
            tmp_path = f.name

        try:
            result = update_log_stats(tmp_path, '2026-05-12T12:00:00+08:00')
            assert result is False
        finally:
            os.unlink(tmp_path)

    def test_file_not_found(self):
        result = update_log_stats('/nonexistent/path.md', '2026-05-12T12:00:00+08:00')
        assert result is False


class TestFindInWorkspace:

    def test_finds_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'subdir').mkdir()
            (Path(tmp) / 'subdir' / 'target.md').write_text('hello')

            result = find_in_workspace('target.md', str(tmp))
            assert result is not None
            assert 'target.md' in result

    def test_file_not_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = find_in_workspace('nonexistent.md', str(tmp))
            assert result is None

    def test_search_root_not_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.rmdir(tmp)
            result = find_in_workspace('test.md', tmp)
            assert result is None

    def test_fd_binary_not_available(self, monkeypatch):
        def mock_run(*args, **kwargs):
            raise FileNotFoundError('fd not found')
        monkeypatch.setattr(subprocess, 'run', mock_run)
        with tempfile.TemporaryDirectory() as tmp:
            result = find_in_workspace('test.md', str(tmp))
            assert result is None


class TestMainPathValidation:

    SCRIPT = str(
        Path(__file__).parent.parent
        / 'skills' / 'log-memory-searcher' / 'scripts' / 'dream-stats-updater.py'
    )

    def _run(self, *args):
        result = subprocess.run(
            [sys.executable, self.SCRIPT, *args],
            capture_output=True, text=True
        )
        return result

    def test_report_relative_path_rejected(self):
        result = self._run(
            '--report', 'relative/path/report.md',
            '--log-base', str(Path(tempfile.gettempdir())),
        )
        assert result.returncode != 0
        assert '必须是绝对路径' in result.stdout

    def test_log_base_relative_path_rejected(self):
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as f:
            f.write(b'---\ntype: dream\npath_visited: []\n---\n')
            report_path = f.name
        try:
            result = self._run(
                '--report', report_path,
                '--log-base', 'relative/path',
            )
            assert result.returncode != 0
            assert '必须是绝对路径' in result.stdout
        finally:
            os.unlink(report_path)

    def test_log_base_not_a_directory_rejected(self):
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as f:
            f.write(b'---\ntype: dream\npath_visited: []\n---\n')
            report_path = f.name
        try:
            result = self._run(
                '--report', report_path,
                '--log-base', report_path,
            )
            assert result.returncode != 0
            assert '必须是一个存在的目录' in result.stdout
        finally:
            os.unlink(report_path)


class TestCompactArrayEncoder:

    def _encode(self, obj):
        return json.dumps(obj, ensure_ascii=False, indent=2, cls=CompactArrayEncoder)

    def _roundtrip(self, obj):
        encoded = self._encode(obj)
        decoded = json.loads(encoded)
        return encoded, decoded

    def test_simple_dict_with_string_list(self):
        obj = {
            "title": "Test",
            "tags": ["#a", "#b", "#c"],
        }
        encoded, decoded = self._roundtrip(obj)
        assert decoded == obj
        assert '"tags": ["#a", "#b", "#c"]' in encoded

    def test_empty_dict(self):
        encoded, decoded = self._roundtrip({})
        assert decoded == {}
        assert encoded == '{}'

    def test_empty_list(self):
        encoded, decoded = self._roundtrip([])
        assert decoded == []
        assert encoded == '[]'

    def test_empty_list_in_dict(self):
        obj = {"items": []}
        encoded, decoded = self._roundtrip(obj)
        assert decoded == obj
        assert '"items": []' in encoded

    def test_boolean_values(self):
        obj = {"active": True, "deleted": False}
        encoded, decoded = self._roundtrip(obj)
        assert decoded == obj
        assert '"active": true' in encoded
        assert '"deleted": false' in encoded

    def test_null_value(self):
        obj = {"value": None}
        encoded, decoded = self._roundtrip(obj)
        assert decoded == obj
        assert '"value": null' in encoded

    def test_integer_value(self):
        obj = {"count": 42}
        encoded, decoded = self._roundtrip(obj)
        assert decoded == obj
        assert '"count": 42' in encoded

    def test_float_value(self):
        obj = {"score": 3.14}
        encoded, decoded = self._roundtrip(obj)
        assert decoded == obj

    def test_nested_dict_in_list(self):
        obj = {
            "items": [
                {"id": 1, "name": "foo"},
                {"id": 2, "name": "bar"},
            ],
        }
        encoded, decoded = self._roundtrip(obj)
        assert decoded == obj
        assert '"items": [' in encoded

    def test_top_level_list_of_dicts(self):
        obj = [
            {"title": "A", "tags": ["#x"]},
            {"title": "B", "tags": ["#y"]},
        ]
        encoded, decoded = self._roundtrip(obj)
        assert decoded == obj
        assert '"tags": ["#x"]' in encoded
        assert '"tags": ["#y"]' in encoded

    def test_mixed_types_in_list(self):
        obj = {"mixed": ["str", 42, True, None]}
        encoded, decoded = self._roundtrip(obj)
        assert decoded == obj
        assert '"mixed": ["str", 42, true, null]' in encoded

    def test_special_float_inf(self):
        obj = {"value": float('inf')}
        encoded, decoded = self._roundtrip(obj)
        assert decoded == obj

    def test_special_float_nan(self):
        obj = {"value": float('nan')}
        encoded, decoded = self._roundtrip(obj)
        assert math.isnan(decoded["value"])

    def test_special_float_neg_inf(self):
        obj = {"value": float('-inf')}
        encoded, decoded = self._roundtrip(obj)
        assert decoded == obj

    def test_deeply_nested(self):
        obj = {
            "level1": {
                "level2": {
                    "tags": ["#deep"],
                },
            },
        }
        encoded, decoded = self._roundtrip(obj)
        assert decoded == obj
        assert '"tags": ["#deep"]' in encoded

    def test_unicode_strings(self):
        obj = {"title": "中文测试", "tags": ["#中文", "#标签"]}
        encoded, decoded = self._roundtrip(obj)
        assert decoded == obj
        assert '"tags": ["#中文", "#标签"]' in encoded

    def test_string_with_special_chars(self):
        obj = {"text": 'hello "world"'}
        encoded, decoded = self._roundtrip(obj)
        assert decoded == obj

    def test_multiple_lists_in_dict(self):
        obj = {
            "tags": ["#a", "#b"],
            "refs": ["x", "y"],
        }
        encoded, decoded = self._roundtrip(obj)
        assert decoded == obj
        assert '"tags": ["#a", "#b"]' in encoded
        assert '"refs": ["x", "y"]' in encoded
