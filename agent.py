#!/usr/bin/env python3
"""
Rebase Agent — Cherry-picks internal-only commits onto upstream, using Claude
to resolve conflicts. Produces a clean linear history with no merge or rebase commits.

Usage:
    python agent.py --internal <internal_repo_url> --upstream <upstream_repo_url> \
                    [--internal-branch main] [--upstream-branch main] \
                    [--github-repo owner/repo] [--push]

Environment variables:
    GITHUB_TOKEN          — GitHub personal access token (for PR context)
    AWS_REGION            — AWS region for Bedrock (default: us-east-1)
    AWS_ACCESS_KEY_ID     — AWS access key (or use AWS CLI/profile/instance role)
    AWS_SECRET_ACCESS_KEY — AWS secret key
    AWS_SESSION_TOKEN     — AWS session token (optional, for temporary credentials)
    TEAMS_WEBHOOK_URL     — Microsoft Teams Incoming Webhook URL (for notifications)
"""

import argparse
import logging
import sys

from config import RebaseConfig
from conflict_resolver import resolve_conflict
from git_ops import GitOperations, InternalCommit
from notifier import RebaseResult, send_teams_notification
from pr_context import fetch_pr_context_for_file

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _notify(config: RebaseConfig, result: RebaseResult):
    """Send Teams notification if webhook is configured."""
    if config.teams_webhook_url:
        send_teams_notification(config.teams_webhook_url, result)


def _make_result(config: RebaseConfig, **kwargs) -> RebaseResult:
    return RebaseResult(
        internal_repo=config.internal_repo_url,
        upstream_repo=config.upstream_repo_url,
        internal_branch=config.internal_branch,
        upstream_branch=config.upstream_branch,
        **kwargs,
    )


def _resolve_cherry_pick_conflicts(
    git: GitOperations,
    config: RebaseConfig,
    commit: InternalCommit,
    resolved_files_all: list[str],
) -> list[str] | None:
    """
    Resolve conflicts for a cherry-pick.
    Returns list of resolved file paths, or None if resolution failed.
    """
    conflicts = git.get_conflicted_files()
    if not conflicts:
        return []

    logger.info("  %d conflicted file(s):", len(conflicts))
    for c in conflicts:
        logger.info("    - %s", c.path)

    round_resolved: list[str] = []
    for conflict in conflicts:
        logger.info("  Fetching PR context for %s...", conflict.path)
        pr_contexts = fetch_pr_context_for_file(config, conflict.path)

        file_log = git.get_file_log(conflict.path)
        if file_log:
            logger.debug("  Recent commits for %s:\n%s", conflict.path, file_log)

        resolved_content = resolve_conflict(config, conflict, pr_contexts)

        if resolved_content is None:
            logger.error("  Failed to resolve %s", conflict.path)
            return None

        git.apply_resolution(conflict.path, resolved_content)
        round_resolved.append(conflict.path)
        resolved_files_all.append(conflict.path)
        logger.info("  Resolved: %s", conflict.path)

    return round_resolved


def run_rebase_agent(config: RebaseConfig, push: bool = False) -> bool:
    """
    Main agent loop:
    1. Clone internal repo, add upstream remote
    2. Find internal-only commits (not in upstream)
    3. Create a new branch from upstream HEAD
    4. Cherry-pick each internal commit onto the new branch
    5. On conflicts: gather PR context, ask Claude to resolve
    6. Result: clean linear history with no merge/rebase commits
    """
    git = GitOperations(config)
    resolved_files: list[str] = []
    branch_name: str | None = None

    try:
        # Step 1: Setup
        logger.info("=== Setting up repositories ===")
        git.clone_internal()
        git.add_upstream_remote()

        # Step 2: Find internal-only commits
        logger.info("=== Finding internal-only commits ===")
        commits = git.get_internal_only_commits()
        if not commits:
            logger.info("No internal-only commits found. Already up to date.")
            _notify(config, _make_result(
                config, success=True, conflicts_resolved=[],
            ))
            return True

        logger.info("Will cherry-pick %d commit(s):", len(commits))
        for i, c in enumerate(commits, 1):
            logger.info("  %d. %s %s", i, c.sha[:8], c.subject)

        # Step 3: Create branch from upstream HEAD
        logger.info("=== Creating branch from upstream ===")
        branch_name = git.create_branch_from_upstream()

        # Step 4: Cherry-pick each commit
        logger.info("=== Cherry-picking internal commits ===")
        for i, commit in enumerate(commits, 1):
            logger.info("--- Commit %d/%d: %s %s ---", i, len(commits), commit.sha[:8], commit.subject)

            pick_result = git.cherry_pick(commit)
            if pick_result is True:
                logger.info("  Applied cleanly.")
                continue
            if pick_result is None:
                # Empty cherry-pick — commit already in upstream, skip
                continue

            # Conflicts — resolve them
            round_resolved = _resolve_cherry_pick_conflicts(
                git, config, commit, resolved_files,
            )

            if round_resolved is None:
                # Resolution failed
                git.abort_cherry_pick()
                _notify(config, _make_result(
                    config,
                    success=False,
                    conflicts_resolved=resolved_files,
                    failed_file=commit.sha[:8],
                    error_message=f"Could not resolve conflicts in commit {commit.sha[:8]}: {commit.subject}",
                    push_branch=branch_name,
                ))
                return False

            # Commit the resolved cherry-pick
            if not git.continue_cherry_pick(commit, resolved_files=round_resolved):
                git.abort_cherry_pick()
                _notify(config, _make_result(
                    config,
                    success=False,
                    conflicts_resolved=resolved_files,
                    error_message=f"Failed to commit resolved cherry-pick for {commit.sha[:8]}",
                    push_branch=branch_name,
                ))
                return False

            logger.info("  Committed with [Conflict resolved] tag.")

        # Step 5: Done!
        logger.info("=== All %d commits cherry-picked successfully! ===", len(commits))
        logger.info("Result branch: %s", branch_name)

        if push:
            git.push_result(branch_name)

        _notify(config, _make_result(
            config,
            success=True,
            conflicts_resolved=resolved_files,
            push_branch=branch_name,
        ))
        return True

    except Exception as e:
        _notify(config, _make_result(
            config,
            success=False,
            conflicts_resolved=resolved_files,
            error_message=str(e),
            push_branch=branch_name,
        ))
        raise

    finally:
        git.cleanup()


def main():
    parser = argparse.ArgumentParser(
        description="Cherry-pick internal commits onto upstream with AI-powered conflict resolution"
    )
    parser.add_argument("--internal", required=True, help="Internal repo URL")
    parser.add_argument("--upstream", required=True, help="Upstream repo URL")
    parser.add_argument("--internal-branch", default="main", help="Internal branch (default: main)")
    parser.add_argument("--upstream-branch", default="main", help="Upstream branch (default: main)")
    parser.add_argument("--internal-start", default="", help="Internal commit SHA to start cherry-picking from (inclusive, through branch HEAD)")
    parser.add_argument("--github-repo", default="", help="GitHub repo for PR context (owner/repo)")
    parser.add_argument("--upstream-base", default="", help="Specific upstream commit SHA or tag to use as rebase base (default: upstream branch HEAD)")
    parser.add_argument("--push", action="store_true", help="Push result after successful cherry-pick")
    parser.add_argument("--work-dir", default="", help="Working directory (default: temp dir)")
    parser.add_argument("--model", default="us.anthropic.claude-opus-4-6-v1", help="Bedrock model ID")
    parser.add_argument("--aws-region", default="", help="AWS region for Bedrock (default: us-east-1)")
    parser.add_argument("--max-prs", type=int, default=10, help="Max PRs to fetch per file")
    parser.add_argument("--teams-webhook", default="", help="Microsoft Teams Incoming Webhook URL")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    config = RebaseConfig(
        internal_repo_url=args.internal,
        upstream_repo_url=args.upstream,
        internal_branch=args.internal_branch,
        internal_start=args.internal_start,
        upstream_branch=args.upstream_branch,
        upstream_base=args.upstream_base,
        github_internal_repo=args.github_repo,
        work_dir=args.work_dir,
        claude_model=args.model,
        aws_region=args.aws_region,
        max_prs_per_file=args.max_prs,
        teams_webhook_url=args.teams_webhook,
    )

    success = run_rebase_agent(config, push=args.push)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
