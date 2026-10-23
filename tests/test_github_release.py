"""Release gates consume exact SDK evidence, not shell exit codes."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from scripts.github_release import ReleaseCheck, verify_github_release


@pytest.mark.parametrize(
    ("state", "context"),
    [("failure", "release-artifacts"), ("pending", "release-artifacts"), ("success", "other")],
)
def test_missing_or_failed_artifact_gate_is_rejected(state, context):
    repository = Mock()
    repository.get_commit.return_value.get_combined_status.return_value.statuses = [
        SimpleNamespace(context=context, state=state)
    ]
    with pytest.raises(ValueError, match="release-artifacts"):
        verify_github_release(ReleaseCheck(revision="a" * 40), repository=repository)


def test_published_tag_and_status_are_bound_to_exact_commit():
    repository = Mock()
    repository.get_release.return_value = SimpleNamespace(draft=False, tag_name="v0.1.0")
    repository.get_commit.return_value.sha = "a" * 40
    repository.get_commit.return_value.get_combined_status.return_value.statuses = [
        SimpleNamespace(context="release-artifacts", state="success")
    ]
    request = ReleaseCheck(revision="a" * 40, release="v0.1.0")
    assert verify_github_release(request, repository=repository).revision == "a" * 40
    repository.get_commit.return_value.sha = "b" * 40
    with pytest.raises(ValueError, match="differs"):
        verify_github_release(request, repository=repository)
    repository.get_release.return_value.draft = True
    with pytest.raises(ValueError, match="not published"):
        verify_github_release(request, repository=repository)
