"""Fetch past PR context from GitHub for conflict resolution hints."""

import logging
from dataclasses import dataclass

from github import Github

from config import RebaseConfig

logger = logging.getLogger(__name__)


@dataclass
class PRContext:
    number: int
    title: str
    body: str
    diff_for_file: str  # The diff within this PR for the conflicted file
    merged_at: str


def fetch_pr_context_for_file(
    config: RebaseConfig, filepath: str
) -> list[PRContext]:
    """
    Find merged PRs in the internal repo that touched `filepath`.
    Returns PR metadata + the relevant diff snippet.
    """
    if not config.github_token or not config.github_internal_repo:
        logger.warning("GitHub token or repo not configured — skipping PR context")
        return []

    g = Github(config.github_token)
    repo = g.get_repo(config.github_internal_repo)

    contexts = []
    # Search merged PRs that touched this file
    # GitHub search API: use the repo's pulls endpoint with file filter
    pulls = repo.get_pulls(state="closed", sort="updated", direction="desc")

    checked = 0
    for pr in pulls:
        if checked >= config.max_prs_per_file * 5:
            # Don't scan too many PRs
            break
        if not pr.merged:
            checked += 1
            continue

        # Check if this PR touched the file
        try:
            files = pr.get_files()
            matching_file = None
            for f in files:
                if f.filename == filepath:
                    matching_file = f
                    break

            if matching_file is None:
                checked += 1
                continue

            contexts.append(PRContext(
                number=pr.number,
                title=pr.title,
                body=(pr.body or "")[:2000],  # Truncate long bodies
                diff_for_file=matching_file.patch or "",
                merged_at=str(pr.merged_at),
            ))

            if len(contexts) >= config.max_prs_per_file:
                break
        except Exception as e:
            logger.debug("Error reading PR #%d: %s", pr.number, e)

        checked += 1

    logger.info("Found %d relevant PRs for %s", len(contexts), filepath)
    return contexts
