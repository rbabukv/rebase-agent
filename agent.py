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
from dataclasses import dataclass
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

from config import RebaseConfig
from conflict_resolver import ResolutionResult, resolve_conflict
from git_ops import GitOperations, InternalCommit, UpstreamCommit
from notifier import ConfidenceEntry, RebaseResult, send_teams_notification
from pr_context import fetch_pr_context_for_file

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class FileConfidence:
    path: str
    commit_sha: str
    confidence: int  # 0-100, or -1 if unknown
    reasoning: str


@dataclass
class SkippedCommit:
    commit: InternalCommit
    upstream_sha: str
    upstream_subject: str
    similarity: float  # 0.0 to 1.0


@dataclass
class CommitOutcome:
    """Tracks the outcome of each commit during the cherry-pick loop."""
    commit: InternalCommit
    status: str  # "Clean", "Conflict", "Skipped (upstream match)", "Skipped (empty)"
    confidence: str = "—"  # e.g., "85%", "90-95% (2 files)", "—"
    rebase_sha: str = "—"  # SHA on the rebased branch, or "—" if skipped


def _find_upstream_match(
    subject: str, upstream_commits: list[UpstreamCommit], threshold: float = 0.85,
) -> tuple[UpstreamCommit, float] | None:
    """Find the best matching upstream commit by subject similarity (>threshold)."""
    best_match = None
    best_ratio = 0.0
    for uc in upstream_commits:
        ratio = SequenceMatcher(None, subject.lower(), uc.subject.lower()).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = uc
    if best_match and best_ratio > threshold:
        return (best_match, best_ratio)
    return None


def _notify(config: RebaseConfig, result: RebaseResult):
    """Send Teams notification if webhook is configured."""
    if config.teams_webhook_url:
        send_teams_notification(config.teams_webhook_url, result)


def _log_confidence_summary(scores: list[FileConfidence]):
    """Print a confidence score summary table."""
    logger.info("=== Conflict Resolution Confidence Summary ===")
    logger.info("%-50s %-10s %-6s %s", "File", "Commit", "Score", "Reasoning")
    logger.info("-" * 110)
    for s in sorted(scores, key=lambda x: x.confidence):
        score_str = f"{s.confidence}%" if s.confidence >= 0 else "N/A"
        logger.info("%-50s %-10s %-6s %s", s.path, s.commit_sha, score_str, s.reasoning)

    valid = [s.confidence for s in scores if s.confidence >= 0]
    if valid:
        avg = sum(valid) / len(valid)
        low = [s for s in scores if 0 <= s.confidence < 70]
        logger.info("-" * 110)
        logger.info(
            "Average confidence: %.0f%% | Files resolved: %d | Needs review (< 70%%): %d",
            avg, len(scores), len(low),
        )
        if low:
            logger.warning("Files recommended for manual review:")
            for s in low:
                logger.warning("  - %s (commit %s, %d%%): %s", s.path, s.commit_sha, s.confidence, s.reasoning)


def _log_commit_breakdown(outcomes: list[CommitOutcome]):
    """Print a per-commit breakdown table showing status of all commits."""
    logger.info("=== Per-Commit Breakdown ===")
    logger.info(
        "%-4s %-12s %-12s %-45s %-26s %s",
        "#", "Internal SHA", "Rebase SHA", "Description", "Status", "Confidence",
    )
    logger.info("-" * 150)

    clean_count = 0
    conflict_count = 0
    skipped_match_count = 0
    skipped_empty_count = 0

    for i, o in enumerate(outcomes, 1):
        desc = o.commit.subject[:45]
        logger.info(
            "%-4d %-12s %-12s %-45s %-26s %s",
            i, o.commit.sha[:8], o.rebase_sha, desc, o.status, o.confidence,
        )
        if o.status == "Clean":
            clean_count += 1
        elif o.status == "Conflict":
            conflict_count += 1
        elif o.status.startswith("Skipped (upstream"):
            skipped_match_count += 1
        elif o.status.startswith("Skipped (empty"):
            skipped_empty_count += 1

    logger.info("-" * 150)
    parts = [f"Total: {len(outcomes)}"]
    if clean_count:
        parts.append(f"Clean: {clean_count}")
    if conflict_count:
        parts.append(f"Conflicts resolved: {conflict_count}")
    if skipped_match_count:
        parts.append(f"Skipped (upstream match): {skipped_match_count}")
    if skipped_empty_count:
        parts.append(f"Skipped (empty): {skipped_empty_count}")
    logger.info(" | ".join(parts))


def _generate_confidence_md(
    config: RebaseConfig,
    branch_name: str,
    outcomes: list[CommitOutcome],
    confidence_scores: list[FileConfidence],
    skipped_commits: list[SkippedCommit],
) -> str:
    """Generate a markdown confidence report and return its content."""
    lines: list[str] = []
    upstream_label = config.upstream_base or config.upstream_branch
    lines.append(f"# Rebase Confidence Scoring — {upstream_label}")
    lines.append("")
    lines.append(f"**Branch:** `{branch_name}`  ")
    lines.append(f"**Date:** {date.today().isoformat()}  ")
    lines.append(f"**Upstream base:** `{upstream_label}`  ")
    if config.internal_start:
        lines.append(f"**Internal start:** `{config.internal_start[:8]}`")
    lines.append("")

    # --- Per-Commit Breakdown ---
    lines.append("## Per-Commit Breakdown")
    lines.append("")
    lines.append("| # | Internal SHA | Rebase SHA | Description | Status | Confidence |")
    lines.append("|---|-------------|------------|-------------|--------|------------|")
    for i, o in enumerate(outcomes, 1):
        sha = o.commit.sha[:8]
        rebase = f"`{o.rebase_sha}`" if o.rebase_sha != "—" else "—"
        desc = o.commit.subject
        status = o.status
        conf = o.confidence
        # Bold low-confidence scores in the confidence column
        lines.append(f"| {i} | `{sha}` | {rebase} | {desc} | {status} | {conf} |")
    lines.append("")

    # --- Summary ---
    clean_count = sum(1 for o in outcomes if o.status == "Clean")
    conflict_count = sum(1 for o in outcomes if o.status == "Conflict")
    skipped_empty_count = sum(1 for o in outcomes if o.status.startswith("Skipped (empty"))
    skipped_match_count = len(skipped_commits)

    valid_scores = [s.confidence for s in confidence_scores if s.confidence >= 0]
    avg_conf = sum(valid_scores) / len(valid_scores) if valid_scores else 0

    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total commits | {len(outcomes)} |")
    lines.append(f"| Clean cherry-picks | {clean_count} |")
    if skipped_empty_count:
        lines.append(f"| Skipped (empty cherry-pick) | {skipped_empty_count} |")
    if skipped_match_count:
        lines.append(f"| Skipped (upstream match) | {skipped_match_count} |")
    lines.append(f"| Conflicts resolved | {conflict_count} |")
    lines.append(f"| Total files resolved | {len(confidence_scores)} |")
    lines.append(f"| Average confidence | **{avg_conf:.0f}%** |")
    lines.append("")

    # --- Skipped Commits — Upstream Match Details ---
    if skipped_commits:
        lines.append("## Skipped Commits — Upstream Match Details")
        lines.append("")
        lines.append("| Internal SHA | Internal Subject | Upstream SHA | Upstream Subject | Similarity |")
        lines.append("|-------------|-----------------|-------------|-----------------|------------|")
        for sc in skipped_commits:
            lines.append(
                f"| `{sc.commit.sha[:8]}` | {sc.commit.subject} "
                f"| `{sc.upstream_sha[:8]}` | {sc.upstream_subject} | {sc.similarity:.0%} |"
            )
        lines.append("")

    # --- Files Needing Manual Review ---
    low_conf = [s for s in confidence_scores if 0 <= s.confidence < 70]
    na_conf = [s for s in confidence_scores if s.confidence < 0]
    review_files = low_conf + na_conf
    if review_files:
        lines.append("## Files Needing Manual Review (< 70%)")
        lines.append("")
        lines.append("| File | Confidence | Internal SHA | Rebase SHA |")
        lines.append("|------|------------|-------------|------------|")
        for s in sorted(review_files, key=lambda x: x.confidence):
            score_str = f"**{s.confidence}%**" if s.confidence >= 0 else "**N/A**"
            # Find the matching outcome to get commit subject and rebase SHA
            matching = [o for o in outcomes if o.commit.sha[:8] == s.commit_sha]
            subject = matching[0].commit.subject if matching else ""
            rebase = f"`{matching[0].rebase_sha}`" if matching and matching[0].rebase_sha != "—" else "—"
            lines.append(f"| `{s.path}` | {score_str} | `{s.commit_sha}` — {subject} | {rebase} |")
        lines.append("")

    return "\n".join(lines)


def _make_result(config: RebaseConfig, **kwargs) -> RebaseResult:
    # Convert FileConfidence to ConfidenceEntry for the notifier
    if "confidence_scores" in kwargs and kwargs["confidence_scores"]:
        kwargs["confidence_scores"] = [
            ConfidenceEntry(
                path=fc.path,
                commit_sha=fc.commit_sha,
                confidence=fc.confidence,
                reasoning=fc.reasoning,
            )
            for fc in kwargs["confidence_scores"]
        ]
    # Convert SkippedCommit to SkippedEntry for the notifier
    if "skipped_commits" in kwargs and kwargs["skipped_commits"]:
        from notifier import SkippedEntry
        kwargs["skipped_commits"] = [
            SkippedEntry(
                internal_sha=sc.commit.sha[:8],
                internal_subject=sc.commit.subject,
                upstream_sha=sc.upstream_sha[:8],
                upstream_subject=sc.upstream_subject,
                similarity=sc.similarity,
            )
            for sc in kwargs["skipped_commits"]
        ]
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
    confidence_scores: list[FileConfidence],
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

        result = resolve_conflict(config, conflict, pr_contexts)

        if result is None:
            logger.error("  Failed to resolve %s", conflict.path)
            return None

        git.apply_resolution(conflict.path, result.content)
        round_resolved.append(conflict.path)
        resolved_files_all.append(conflict.path)
        confidence_scores.append(FileConfidence(
            path=conflict.path,
            commit_sha=commit.sha[:8],
            confidence=result.confidence,
            reasoning=result.reasoning,
        ))
        logger.info("  Resolved: %s (confidence: %d%%)", conflict.path, result.confidence)

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
    confidence_scores: list[FileConfidence] = []
    skipped_commits: list[SkippedCommit] = []
    commit_outcomes: list[CommitOutcome] = []
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

        # Step 2b: Fetch upstream commit subjects for similarity matching
        logger.info("=== Fetching upstream commit subjects (last 1 year) ===")
        upstream_commits = git.get_upstream_commit_subjects(since_days=365)

        # Step 3: Create branch from upstream HEAD
        logger.info("=== Creating branch from upstream ===")
        branch_name = git.create_branch_from_upstream()

        # Step 4: Cherry-pick each commit
        logger.info("=== Cherry-picking internal commits ===")
        for i, commit in enumerate(commits, 1):
            logger.info("--- Commit %d/%d: %s %s ---", i, len(commits), commit.sha[:8], commit.subject)

            # Check if commit subject matches an upstream commit (>85% similarity)
            if upstream_commits:
                match = _find_upstream_match(commit.subject, upstream_commits)
                if match:
                    upstream_commit, similarity = match
                    logger.info(
                        "  Skipping — upstream match (%.0f%%): %s %s",
                        similarity * 100, upstream_commit.sha[:8], upstream_commit.subject,
                    )
                    skipped_commits.append(SkippedCommit(
                        commit=commit,
                        upstream_sha=upstream_commit.sha,
                        upstream_subject=upstream_commit.subject,
                        similarity=similarity,
                    ))
                    commit_outcomes.append(CommitOutcome(
                        commit=commit,
                        status=f"Skipped (upstream match → {upstream_commit.sha[:8]})",
                        confidence=f"{similarity:.0%} similar",
                    ))
                    continue

            pick_result = git.cherry_pick(commit)
            if pick_result is True:
                rebase_sha = git.get_head_sha()
                logger.info("  Applied cleanly.")
                commit_outcomes.append(CommitOutcome(
                    commit=commit, status="Clean",
                    rebase_sha=rebase_sha,
                ))
                continue
            if pick_result is None:
                # Empty cherry-pick — commit already in upstream, skip
                commit_outcomes.append(CommitOutcome(
                    commit=commit, status="Skipped (empty cherry-pick)",
                ))
                continue

            # Conflicts — resolve them
            round_resolved = _resolve_cherry_pick_conflicts(
                git, config, commit, resolved_files, confidence_scores,
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

            # Build confidence detail for this commit
            rebase_sha = git.get_head_sha()
            commit_conf = [s for s in confidence_scores if s.commit_sha == commit.sha[:8]]
            if len(commit_conf) == 1:
                conf_detail = f"{commit_conf[0].confidence}%"
            elif len(commit_conf) > 1:
                scores_vals = [s.confidence for s in commit_conf if s.confidence >= 0]
                if scores_vals:
                    lo, hi = min(scores_vals), max(scores_vals)
                    conf_detail = f"{lo}-{hi}% ({len(commit_conf)} files)"
                else:
                    conf_detail = f"N/A ({len(commit_conf)} files)"
            else:
                conf_detail = "Resolved"

            commit_outcomes.append(CommitOutcome(
                commit=commit, status="Conflict",
                confidence=conf_detail, rebase_sha=rebase_sha,
            ))
            logger.info("  Committed with [Conflict resolved] tag.")

        # Step 5: Done!
        logger.info("=== All %d commits cherry-picked successfully! ===", len(commits))
        logger.info("Result branch: %s", branch_name)

        # Print per-commit breakdown table (includes skipped commits)
        if commit_outcomes:
            _log_commit_breakdown(commit_outcomes)

        # Print confidence summary
        if confidence_scores:
            _log_confidence_summary(confidence_scores)

        # Generate and write confidence markdown report
        md_content = _generate_confidence_md(
            config, branch_name, commit_outcomes,
            confidence_scores, skipped_commits,
        )
        upstream_label = config.upstream_base or config.upstream_branch
        md_filename = f"rebase_confidence_{upstream_label}.md"
        md_path = Path(md_filename)
        md_path.write_text(md_content)
        logger.info("Confidence report written to %s", md_filename)
        print(f"\n{md_content}")

        if push:
            git.push_result(branch_name)

        _notify(config, _make_result(
            config,
            success=True,
            conflicts_resolved=resolved_files,
            confidence_scores=confidence_scores,
            skipped_commits=skipped_commits,
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
