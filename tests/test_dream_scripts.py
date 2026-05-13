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


dream_hint_selector = importlib.import_module('dream-hint-selector')
compute_weight = dream_hint_selector.compute_weight
is_in_cooldown = dream_hint_selector.is_in_cooldown
_parse_iso_datetime = dream_hint_selector._parse_iso_datetime
load_hints = dream_hint_selector.load_hints
save_hints = dream_hint_selector.save_hints
select_hint = dream_hint_selector.select_hint
NO_HINT_PROBABILITY = dream_hint_selector.NO_HINT_PROBABILITY


class TestParseIsoDatetime:

    def test_valid_iso_with_timezone(self):
        result = _parse_iso_datetime('2026-05-14T12:00:00+08:00')
        assert result is not None
        assert result.year == 2026
        assert result.month == 5
        assert result.day == 14

    def test_valid_iso_with_z(self):
        result = _parse_iso_datetime('2026-05-14T12:00:00Z')
        assert result is not None
        assert result.hour == 12

    def test_none_returns_none(self):
        assert _parse_iso_datetime(None) is None

    def test_null_string_returns_none(self):
        assert _parse_iso_datetime('null') is None
        assert _parse_iso_datetime('None') is None

    def test_empty_string_returns_none(self):
        assert _parse_iso_datetime('') is None

    def test_invalid_string_returns_none(self):
        assert _parse_iso_datetime('not-a-date') is None

    def test_datetime_object_passthrough(self):
        from datetime import datetime, timezone, timedelta
        tz = timezone(timedelta(hours=8))
        dt = datetime(2026, 5, 14, 12, 0, 0, tzinfo=tz)
        result = _parse_iso_datetime(dt)
        assert result == dt


class TestComputeWeight:

    def test_disposable_hint_returns_priority(self):
        hint = {'priority': 3, 'cooldown_days': 0}
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone(timedelta(hours=8)))
        assert compute_weight(hint, now) == 3.0

    def test_disposable_hint_default_priority(self):
        hint = {'cooldown_days': 0}
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone(timedelta(hours=8)))
        assert compute_weight(hint, now) == 1.0

    def test_persistent_hint_never_used(self):
        hint = {'priority': 2, 'cooldown_days': 10, 'last_used': None}
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone(timedelta(hours=8)))
        weight = compute_weight(hint, now)
        assert weight == 2.0 * (1 + 10.0 / 10.0)
        assert weight == 4.0

    def test_persistent_hint_past_cooldown(self):
        hint = {
            'priority': 2,
            'cooldown_days': 10,
            'last_used': '2026-05-01T00:00:00+08:00',
        }
        from datetime import datetime, timezone, timedelta
        tz = timezone(timedelta(hours=8))
        now = datetime(2026, 5, 14, 0, 0, 0, tzinfo=tz)
        weight = compute_weight(hint, now)
        elapsed = 13.0
        days_since = elapsed - 10
        expected = 2.0 * (1 + days_since / 10.0)
        assert weight == pytest.approx(expected)

    def test_persistent_hint_in_cooldown_still_returns_weight(self):
        hint = {
            'priority': 2,
            'cooldown_days': 10,
            'last_used': '2026-05-10T00:00:00+08:00',
        }
        from datetime import datetime, timezone, timedelta
        tz = timezone(timedelta(hours=8))
        now = datetime(2026, 5, 14, 0, 0, 0, tzinfo=tz)
        weight = compute_weight(hint, now)
        elapsed = 4.0
        days_since = max(0, elapsed - 10)
        expected = 2.0 * (1 + days_since / 10.0)
        assert weight == pytest.approx(2.0)

    def test_persistent_hint_invalid_last_used(self):
        hint = {
            'priority': 2,
            'cooldown_days': 10,
            'last_used': 'not-a-date',
        }
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone(timedelta(hours=8)))
        weight = compute_weight(hint, now)
        assert weight == 2.0


class TestIsInCooldown:

    def test_disposable_hint_never_in_cooldown(self):
        hint = {'cooldown_days': 0, 'last_used': '2026-05-14T00:00:00+08:00'}
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone(timedelta(hours=8)))
        assert is_in_cooldown(hint, now) is False

    def test_persistent_hint_in_cooldown(self):
        hint = {
            'cooldown_days': 10,
            'last_used': '2026-05-10T00:00:00+08:00',
        }
        from datetime import datetime, timezone, timedelta
        tz = timezone(timedelta(hours=8))
        now = datetime(2026, 5, 14, 0, 0, 0, tzinfo=tz)
        assert is_in_cooldown(hint, now) is True

    def test_persistent_hint_past_cooldown(self):
        hint = {
            'cooldown_days': 10,
            'last_used': '2026-05-01T00:00:00+08:00',
        }
        from datetime import datetime, timezone, timedelta
        tz = timezone(timedelta(hours=8))
        now = datetime(2026, 5, 14, 0, 0, 0, tzinfo=tz)
        assert is_in_cooldown(hint, now) is False

    def test_never_used_not_in_cooldown(self):
        hint = {'cooldown_days': 10, 'last_used': None}
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone(timedelta(hours=8)))
        assert is_in_cooldown(hint, now) is False


class TestLoadSaveHints:

    def test_load_nonexistent_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = load_hints(Path(tmp) / 'nonexistent.yaml')
            assert result is None

    def test_save_and_load_roundtrip(self):
        hints = [
            {
                'description': 'test hint',
                'type': 'perspective',
                'cooldown_days': 0,
                'priority': 2,
                'last_used': None,
                'disposable': True,
                'associated_reports': ['2026/05/14/dream-test.md'],
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            hints_path = Path(tmp) / 'dream-hints.yaml'
            save_hints(hints_path, hints)
            loaded = load_hints(hints_path)
            assert loaded is not None
            assert len(loaded) == 1
            assert loaded[0]['description'] == 'test hint'
            assert loaded[0]['type'] == 'perspective'
            assert loaded[0]['priority'] == 2
            assert loaded[0]['disposable'] is True

    def test_save_and_load_empty_hints(self):
        hints = []
        with tempfile.TemporaryDirectory() as tmp:
            hints_path = Path(tmp) / 'dream-hints.yaml'
            save_hints(hints_path, hints)
            loaded = load_hints(hints_path)
            assert loaded is None


class TestSelectHint:

    def test_no_hints_file_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            dreams_path = Path(tmp)
            result = select_hint(dreams_path)
            assert result == {'selected': None}

    def test_empty_hints_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            dreams_path = Path(tmp)
            save_hints(dreams_path / 'dream-hints.yaml', [])
            result = select_hint(dreams_path)
            assert result == {'selected': None}

    def test_all_in_cooldown_returns_none(self):
        hints = [
            {
                'description': 'cooling down',
                'type': 'task',
                'cooldown_days': 30,
                'priority': 3,
                'last_used': '2026-05-14T00:00:00+08:00',
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            dreams_path = Path(tmp)
            save_hints(dreams_path / 'dream-hints.yaml', hints)
            result = select_hint(dreams_path)
            assert result == {'selected': None}

    def test_single_available_hint_is_selected(self, monkeypatch):
        hints = [
            {
                'description': 'only hint',
                'type': 'perspective',
                'cooldown_days': 0,
                'priority': 3,
                'last_used': None,
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            dreams_path = Path(tmp)
            save_hints(dreams_path / 'dream-hints.yaml', hints)
            monkeypatch.setattr(dream_hint_selector.random, 'uniform', lambda a, b: 0.0)
            result = select_hint(dreams_path)
            assert result['selected'] is not None
            assert result['selected']['description'] == 'only hint'

    def test_no_hint_probability_is_fixed(self):
        hints = []
        for i in range(10):
            hints.append({
                'description': f'hint {i}',
                'type': 'perspective',
                'cooldown_days': 0,
                'priority': 2,
                'last_used': None,
            })

        with tempfile.TemporaryDirectory() as tmp:
            dreams_path = Path(tmp)
            save_hints(dreams_path / 'dream-hints.yaml', hints)

            no_hint_count = 0
            trials = 500
            for _ in range(trials):
                save_hints(dreams_path / 'dream-hints.yaml', hints)
                result = select_hint(dreams_path)
                if result['selected'] is None:
                    no_hint_count += 1

            proportion = no_hint_count / trials
            assert 0.20 <= proportion <= 0.40, (
                f'Expected ~30% no-hint rate, got {proportion*100:.1f}%'
            )
