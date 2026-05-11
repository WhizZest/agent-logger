import sys
import os
import importlib
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'skills' / 'log-memory-searcher' / 'scripts'))

from _yaml_utils import extract_yaml_frontmatter

dream_stats_updater = importlib.import_module('dream-stats-updater')
update_log_stats = dream_stats_updater.update_log_stats
detect_log_base = dream_stats_updater.detect_log_base


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


class TestDetectLogBase:

    def test_finds_dot_log_in_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp) / '.log' / 'dreams' / '2026' / '05'
            log_dir.mkdir(parents=True)
            report = log_dir / 'dream-test.md'
            report.write_text('---\ntype: dream\n---')

            result = detect_log_base(str(report))
            expected = str((Path(tmp) / '.log').resolve())
            assert Path(result).resolve() == Path(expected).resolve()

    def test_no_dot_log_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / 'some' / 'deep' / 'path' / 'report.md'
            report.parent.mkdir(parents=True)
            report.write_text('---\ntype: dream\n---')

            with pytest.raises(SystemExit):
                detect_log_base(str(report))