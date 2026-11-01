"""Contracts exposed by the reusable ReviewGraph composite action."""

from pathlib import Path

ROOT = Path(__file__).parents[1]
ACTION = ROOT / "action.yml"


def test_action_exposes_the_rendered_comment_file():
    action = ACTION.read_text(encoding="utf-8")

    assert "outputs:" in action
    assert "comment-file:" in action
    assert "value: ${{ steps.render.outputs.comment-file }}" in action
    assert "id: render" in action
    assert 'echo "comment-file=${RUNNER_TEMP}/crg-comment.md" >> "${GITHUB_OUTPUT}"' in action
