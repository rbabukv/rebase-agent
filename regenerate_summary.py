#!/usr/bin/env python3
"""
Regenerate rebase summary from the existing log file,
using the updated per-file confidence display format.
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass

# --- Data structures (mirrors agent.py) ---

@dataclass
class InternalCommit:
    sha: str
    subject: str

@dataclass
class FileConfidence:
    path: str
    commit_sha: str
    confidence: int
    reasoning: str

@dataclass
class SkippedCommit:
    commit: InternalCommit
    upstream_sha: str
    upstream_subject: str
    similarity: float

@dataclass
class CommitOutcome:
    commit: InternalCommit
    status: str
    confidence: str = "—"
    rebase_sha: str = "—"


def _repo_web_url(repo_url: str) -> str:
    url = repo_url.rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    if url.startswith("git@"):
        url = url.replace(":", "/", 1).replace("git@", "https://", 1)
    return url


def _commit_link(repo_url: str, sha: str, short: str | None = None) -> str:
    display = short or sha[:8]
    base = _repo_web_url(repo_url)
    return f"[`{display}`]({base}/commit/{sha})"


def parse_log(log_path: str):
    """Parse rebase_run.log to reconstruct all data structures."""
    with open(log_path) as f:
        lines = f.readlines()

    commits: list[InternalCommit] = []
    outcomes: list[CommitOutcome] = []
    confidence_scores: list[FileConfidence] = []
    skipped_commits: list[SkippedCommit] = []

    # Parse commit list from "Will cherry-pick N commit(s):" section
    commit_re = re.compile(r'\s+(\d+)\.\s+([0-9a-f]{8})\s+(.+)$')
    # Parse commit start line
    commit_start_re = re.compile(r'--- Commit (\d+)/(\d+): ([0-9a-f]{8})\s+(.+?) ---$')
    # Parse resolved file
    resolved_re = re.compile(r'Resolved:\s+(\S+)\s+\(confidence:\s+(-?\d+)%\)')
    # Parse "Applied cleanly"
    clean_re = re.compile(r'Applied cleanly\.')
    # Parse "Committed with [Conflict resolved] tag"
    committed_re = re.compile(r'Committed with \[Conflict resolved\] tag\.')
    # Parse upstream match confirmations (empty cherry-pick)
    confirmed_re = re.compile(r'Confirmed upstream match \((\d+)%\):\s+([0-9a-f]{8})\s+(.+)')
    # Parse upstream match with conflicts warning
    upstream_conflict_re = re.compile(r'Subject matched upstream\s+([0-9a-f]{8})\s+\((\d+)%\)\s+but cherry-pick has CONFLICTS')
    # Parse possible upstream match
    possible_match_re = re.compile(r'Possible upstream match \((\d+)%\):\s+([0-9a-f]{8})\s+(.+?)\s+—')

    # Also parse the existing summary to get rebase SHAs (since they're not in the log events)
    existing_summary = Path(log_path).parent / "rebase_summary_v0.5.10.md"

    # Build a map of internal SHA -> rebase SHA from the existing summary
    rebase_sha_map: dict[str, str] = {}
    if existing_summary.exists():
        summary_text = existing_summary.read_text()
        # Match: | N | [`sha8`](url/commit/full_sha) | [`rsha8`](url/commit/full_rebase_sha) | ...
        row_re = re.compile(r'\|\s*\d+\s*\|\s*\[`([0-9a-f]{8})`\]\([^)]+/commit/([0-9a-f]+)\)\s*\|\s*(?:\[`([0-9a-f]{8})`\]\([^)]+/commit/([0-9a-f]+)\)|—)\s*\|')
        for m in row_re.finditer(summary_text):
            int_sha_full = m.group(2)
            rebase_sha_full = m.group(4) or "—"
            rebase_sha_map[int_sha_full[:8]] = rebase_sha_full

    # Phase 1: Collect commits from the "Will cherry-pick" listing
    in_listing = False
    for line in lines:
        if 'Will cherry-pick' in line:
            in_listing = True
            continue
        if in_listing:
            m = commit_re.search(line)
            if m:
                sha8 = m.group(2)
                subject = m.group(3).strip()
                commits.append(InternalCommit(sha=sha8, subject=subject))
            else:
                in_listing = False

    # Phase 2: Walk through the log events to determine outcomes
    current_commit_idx = -1
    current_sha = ""
    current_subject = ""
    current_resolved_files: list[tuple[str, int]] = []  # (path, confidence)
    upstream_match_sha = ""
    upstream_match_subject = ""
    upstream_match_pct = 0
    has_upstream_conflict = False
    outcome_recorded = False  # tracks if current commit got an outcome

    committed_shas: set[str] = set()

    for line in lines:
        # Detect commit start
        m = commit_start_re.search(line)
        if m:
            # Check if previous commit had no outcome (empty cherry-pick)
            if current_sha and not outcome_recorded:
                commit = InternalCommit(sha=current_sha, subject=current_subject)
                outcomes.append(CommitOutcome(
                    commit=commit, status="Skipped (empty cherry-pick)",
                ))
                committed_shas.add(current_sha)

            current_commit_idx = int(m.group(1)) - 1
            current_sha = m.group(3)
            current_subject = m.group(4).strip()
            current_resolved_files = []
            upstream_match_sha = ""
            upstream_match_subject = ""
            upstream_match_pct = 0
            has_upstream_conflict = False
            outcome_recorded = False
            continue

        # Detect possible upstream match
        m = possible_match_re.search(line)
        if m:
            upstream_match_pct = int(m.group(1))
            upstream_match_sha = m.group(2)
            upstream_match_subject = m.group(3).strip()
            continue

        # Detect upstream conflict warning
        m = upstream_conflict_re.search(line)
        if m:
            has_upstream_conflict = True
            continue

        # Detect resolved file
        m = resolved_re.search(line)
        if m:
            fpath = m.group(1)
            conf = int(m.group(2))
            current_resolved_files.append((fpath, conf))
            confidence_scores.append(FileConfidence(
                path=fpath,
                commit_sha=current_sha,
                confidence=conf,
                reasoning="",
            ))
            continue

        # Detect "Applied cleanly"
        if clean_re.search(line):
            commit = InternalCommit(sha=current_sha, subject=current_subject)
            rebase_sha = rebase_sha_map.get(current_sha, "—")
            outcomes.append(CommitOutcome(
                commit=commit, status="Clean",
                rebase_sha=rebase_sha,
            ))
            outcome_recorded = True
            committed_shas.add(current_sha)
            continue

        # Detect "Committed with [Conflict resolved] tag"
        if committed_re.search(line):
            commit = InternalCommit(sha=current_sha, subject=current_subject)
            rebase_sha = rebase_sha_map.get(current_sha, "—")

            # Build confidence detail (per-file)
            if current_resolved_files:
                file_scores = []
                for fp, sc in sorted(current_resolved_files, key=lambda x: x[1]):
                    fname = Path(fp).name
                    score = f"{sc}%" if sc >= 0 else "N/A"
                    file_scores.append(f"{fname}: {score}")
                conf_detail = ", ".join(file_scores)
            else:
                conf_detail = "Resolved"

            if upstream_match_sha:
                status = f"Conflict (upstream match {upstream_match_sha} {upstream_match_pct}%)"
            else:
                status = "Conflict"

            outcomes.append(CommitOutcome(
                commit=commit, status=status,
                confidence=conf_detail, rebase_sha=rebase_sha,
            ))
            outcome_recorded = True
            committed_shas.add(current_sha)
            continue

        # Detect confirmed upstream match (empty cherry-pick, skipped)
        m = confirmed_re.search(line)
        if m:
            pct = int(m.group(1))
            up_sha = m.group(2)
            up_subject = m.group(3).strip()
            commit = InternalCommit(sha=current_sha, subject=current_subject)
            skipped_commits.append(SkippedCommit(
                commit=commit,
                upstream_sha=up_sha,
                upstream_subject=up_subject,
                similarity=pct / 100.0,
            ))
            outcomes.append(CommitOutcome(
                commit=commit,
                status=f"Skipped (upstream match → {up_sha})",
                confidence=f"{pct}% similar",
            ))
            outcome_recorded = True
            committed_shas.add(current_sha)
            continue

        # Detect empty cherry-pick (no upstream match)
        if 'Skipped (empty cherry-pick)' in line and current_commit_idx >= 0:
            # This appears in the breakdown table, not during processing
            pass

    # Handle the very last commit if it had no outcome
    if current_sha and not outcome_recorded:
        commit = InternalCommit(sha=current_sha, subject=current_subject)
        outcomes.append(CommitOutcome(
            commit=commit, status="Skipped (empty cherry-pick)",
        ))
        committed_shas.add(current_sha)

    # Also check for any commits from the initial listing that were missed
    for c in commits:
        if c.sha not in committed_shas:
            outcomes.append(CommitOutcome(
                commit=c, status="Skipped (empty cherry-pick)",
            ))

    # Re-sort outcomes to match original commit order
    sha_order = {c.sha: i for i, c in enumerate(commits)}
    outcomes.sort(key=lambda o: sha_order.get(o.commit.sha, 999))

    return outcomes, confidence_scores, skipped_commits


def generate_summary(
    outcomes: list[CommitOutcome],
    confidence_scores: list[FileConfidence],
    skipped_commits: list[SkippedCommit],
) -> str:
    internal_url = "https://github.com/intel-innersource/frameworks.ai.pytorch.sglang"
    upstream_url = "https://github.com/sgl-project/sglang"
    branch_name = "rebase_20260410181915_1519acf3_4a4a8282"
    upstream_label = "v0.5.10"
    internal_start = "d0eec66"
    command = "python agent.py --internal https://github.com/intel-innersource/frameworks.ai.pytorch.sglang --upstream https://github.com/sgl-project/sglang --internal-branch master_next --upstream-base v0.5.10 --internal-start d0eec66 --work-dir ./workspace"

    lines: list[str] = []
    lines.append(f"# Rebase Summary — {upstream_label}")
    lines.append("")
    lines.append(f"**Branch:** `{branch_name}`  ")
    lines.append(f"**Date:** 2026-04-10  ")
    lines.append(f"**Upstream base:** `{upstream_label}`  ")
    lines.append(f"**Internal start:** `{internal_start}`")
    lines.append("")

    lines.append("## Command")
    lines.append("")
    lines.append("```bash")
    lines.append(command)
    lines.append("```")
    lines.append("")

    # --- Per-Commit Breakdown ---
    lines.append("## Per-Commit Breakdown")
    lines.append("")
    lines.append("| # | Internal SHA | Rebase SHA | Description | Status | Confidence |")
    lines.append("|---|-------------|------------|-------------|--------|------------|")
    for i, o in enumerate(outcomes, 1):
        int_link = _commit_link(internal_url, o.commit.sha)
        rebase = _commit_link(internal_url, o.rebase_sha) if o.rebase_sha != "—" else "—"
        desc = o.commit.subject
        status = o.status
        # For conflicts, show per-file confidence breakdown in markdown
        commit_conf = [s for s in confidence_scores if s.commit_sha == o.commit.sha[:8]]
        if commit_conf:
            file_parts = []
            for fc in sorted(commit_conf, key=lambda x: x.confidence):
                fname = Path(fc.path).name
                score = f"{fc.confidence}%" if fc.confidence >= 0 else "N/A"
                file_parts.append(f"`{fname}`: {score}")
            conf = "<br>".join(file_parts)
        else:
            conf = o.confidence
        lines.append(f"| {i} | {int_link} | {rebase} | {desc} | {status} | {conf} |")
    lines.append("")

    # --- Summary ---
    clean_count = sum(1 for o in outcomes if o.status == "Clean")
    conflict_count = sum(1 for o in outcomes if o.status.startswith("Conflict"))
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

    # --- Skipped Commits ---
    if skipped_commits:
        lines.append("## Skipped Commits — Upstream Match Details")
        lines.append("")
        lines.append("| Internal SHA | Internal Subject | Upstream SHA | Upstream Subject | Similarity |")
        lines.append("|-------------|-----------------|-------------|-----------------|------------|")
        for sc in skipped_commits:
            int_link = _commit_link(internal_url, sc.commit.sha)
            up_link = _commit_link(upstream_url, sc.upstream_sha)
            lines.append(
                f"| {int_link} | {sc.commit.subject} "
                f"| {up_link} | {sc.upstream_subject} | {sc.similarity:.0%} |"
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
            matching = [o for o in outcomes if o.commit.sha[:8] == s.commit_sha[:8]]
            subject = matching[0].commit.subject if matching else ""
            int_link = _commit_link(internal_url, matching[0].commit.sha) if matching else f"`{s.commit_sha}`"
            rebase = _commit_link(internal_url, matching[0].rebase_sha) if matching and matching[0].rebase_sha != "—" else "—"
            lines.append(f"| `{s.path}` | {score_str} | {int_link} — {subject} | {rebase} |")
        lines.append("")

    return "\n".join(lines)


def main():
    log_path = Path(__file__).parent / "rebase_run.log"
    if not log_path.exists():
        print(f"Error: {log_path} not found", file=sys.stderr)
        sys.exit(1)

    outcomes, confidence_scores, skipped_commits = parse_log(str(log_path))

    print(f"Parsed {len(outcomes)} commit outcomes, {len(confidence_scores)} file confidence scores", file=sys.stderr)

    md = generate_summary(outcomes, confidence_scores, skipped_commits)

    out_path = Path(__file__).parent / "rebase_summary_v0.5.10.md"
    out_path.write_text(md)
    print(f"Written to {out_path}", file=sys.stderr)
    print(md)


if __name__ == "__main__":
    main()
