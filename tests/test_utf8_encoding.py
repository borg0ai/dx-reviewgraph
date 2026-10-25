"""#926 - file readers must decode as UTF-8 regardless of system locale."""

from pathlib import Path


class TestUtf8Encoding:
    def _check_encoding(self, filepath):
        source = Path(filepath).read_text(encoding="utf-8")
        return source

    def test_review_reads_utf8(self):
        import inspect

        import graph_engine.tools.review

        source = inspect.getsource(graph_engine.tools.review)
        assert 'read_text(encoding="utf-8"' in source

    def test_flows_tools_reads_utf8(self):
        import inspect

        import graph_engine.tools.flows_tools

        source = inspect.getsource(graph_engine.tools.flows_tools)
        assert 'read_text(encoding="utf-8"' in source

    def test_eval_runner_opens_utf8(self):
        import inspect

        import graph_engine.eval.runner

        source = inspect.getsource(graph_engine.eval.runner)
        assert 'encoding="utf-8"' in source

    def test_eval_reporter_opens_utf8(self):
        import inspect

        import graph_engine.eval.reporter

        source = inspect.getsource(graph_engine.eval.reporter)
        assert 'encoding="utf-8"' in source
