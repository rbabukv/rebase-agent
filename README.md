# Rebase Agent

Automated tool for rebasing an internal fork onto upstream, using Claude (via AWS Bedrock) to resolve cherry-pick conflicts.

## What It Does

Rebase Agent cherry-picks internal-only commits onto the latest upstream branch, producing a clean linear history with no merge commits. When conflicts arise, it uses Claude to resolve them automatically, scoring each resolution with a confidence percentage.

## Features

### AI-Powered Conflict Resolution
- Uses Claude (via AWS Bedrock) to resolve cherry-pick conflicts
- Provides each conflicted file with the full conflict markers, ours/theirs/base versions, and PR context from GitHub
- Two resolution modes:
  - **Full-file mode** (files < 40KB): Sends the entire file to Claude in one call
  - **Chunk mode** (files >= 40KB): Resolves each conflict block independently
- Trivial conflicts (one side empty) are resolved automatically without calling Claude

### Confidence Scoring
Each conflict resolution gets a confidence score (0-100%):

| Range | Meaning |
|-------|---------|
| 90-100% | Trivial/mechanical (e.g., import reordering, whitespace) |
| 70-89% | Moderate (clear intent, some judgment required) |
| 50-69% | Complex (multiple valid resolutions possible) |
| 0-49% | Significant uncertainty (manual review recommended) |

For chunk mode, the minimum score across all blocks is used (weakest-link principle).

### Upstream Duplicate Detection
Before cherry-picking, the agent fetches upstream commit subjects from the last year and compares them using fuzzy string matching (`difflib.SequenceMatcher`, >85% threshold). However, **subject matching alone never skips a commit** — the agent always attempts the cherry-pick and lets git confirm:

| Subject Match? | Cherry-pick Result | Behavior |
|---|---|---|
| No | Clean | Apply normally |
| No | Empty | Skip (git confirmed duplicate) |
| Yes | Empty | Skip + record upstream match details |
| Yes | Clean | **Keep commit** + warn that content differs despite similar subject |
| Yes | Conflict | **Warn strongly** + resolve, flag for manual review |

### PR Context Fetching
For each conflicted file, the agent searches merged PRs in the internal GitHub repo that touched that file, providing Claude with PR titles, descriptions, and diffs as additional context for resolution.

### Rebase Summary Report
After a successful rebase, the agent generates a detailed markdown report (`rebase_summary_<upstream_label>.md`) containing:
- The exact command used to run the rebase
- Per-commit breakdown table with clickable GitHub commit links for both internal and rebased SHAs
- Per-file confidence scores for each conflict resolution (e.g., `template_manager.py: 90%`, `flux.py: 52%`)
- Summary statistics (clean/conflict/skipped counts, average confidence)
- Skipped commits with upstream match details and similarity scores
- Files needing manual review (confidence < 70%)

A standalone `regenerate_summary.py` script can re-parse `rebase_run.log` and regenerate the summary report without re-running the full rebase.

### Microsoft Teams Notifications
Optional webhook integration sends an Adaptive Card to Teams with rebase results, including success/failure status, resolved files, confidence scores, and files needing review.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Requirements
- Python 3.12+
- Git
- AWS credentials configured (for Claude via Bedrock)

### Dependencies
- `anthropic[bedrock]` — Claude API client with AWS Bedrock support
- `PyGithub` — GitHub API client for PR context fetching

## Usage

```bash
python agent.py \
  --internal <internal_repo_url> \
  --upstream <upstream_repo_url> \
  [options]
```

### Required Arguments

| Argument | Description |
|----------|-------------|
| `--internal` | Internal (fork) repo URL |
| `--upstream` | Upstream repo URL |

### Optional Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--internal-branch` | `main` | Internal branch to cherry-pick from |
| `--upstream-branch` | `main` | Upstream branch to rebase onto |
| `--upstream-base` | branch HEAD | Specific upstream commit SHA or tag to use as rebase base |
| `--internal-start` | — | Start cherry-picking from this SHA (inclusive) through branch HEAD |
| `--github-repo` | auto-detected | GitHub repo for PR context (`owner/repo` format) |
| `--push` | off | Push the result branch to origin after success |
| `--work-dir` | temp dir | Working directory for the clone |
| `--model` | `us.anthropic.claude-opus-4-6-v1` | Bedrock model ID for conflict resolution |
| `--aws-region` | `us-east-1` | AWS region for Bedrock |
| `--max-prs` | `10` | Max PRs to fetch per conflicted file |
| `--teams-webhook` | — | Microsoft Teams Incoming Webhook URL |
| `-v, --verbose` | off | Enable debug logging |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub personal access token with `repo` scope — used to fetch merged PR metadata (titles, descriptions, diffs) for conflicted files, giving Claude better context for resolution. Without this, conflict resolution still works but without PR context. |
| `AWS_REGION` | AWS region for Bedrock |
| `AWS_ACCESS_KEY_ID` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `AWS_SESSION_TOKEN` | AWS session token (optional, for temporary credentials) |
| `TEAMS_WEBHOOK_URL` | Microsoft Teams webhook URL |

### Example

```bash
# Rebase internal fork onto upstream tag v0.5.10, starting from a specific commit
python agent.py \
  --internal git@github.com:myorg/myrepo.git \
  --upstream https://github.com/upstream/repo.git \
  --upstream-base v0.5.10 \
  --internal-start d0eec66 \
  --work-dir ./workspace \
  --push
```

## Output

### Terminal
- Per-commit breakdown table showing status (Clean/Conflict/Skipped) and confidence scores
- Confidence summary with average score and files needing review

### Files
- `rebase_summary_<upstream_label>.md` — Rebase summary report with per-commit breakdown, confidence scores, and the command used

### Git
- A new branch named `rebase_<timestamp>_<upstream_sha>_<internal_sha>` containing the rebased commits

## Project Structure

```
rebase-agent/
  agent.py                # Main orchestrator — cherry-pick loop, reporting
  git_ops.py              # Git operations wrapper (clone, cherry-pick, conflict detection)
  conflict_resolver.py    # Claude-powered conflict resolution with confidence scoring
  pr_context.py           # GitHub PR context fetching for conflicted files
  notifier.py             # Microsoft Teams webhook notifications
  config.py               # Configuration dataclass
  regenerate_summary.py   # Re-parse logs and regenerate the summary report
  requirements.txt        # Python dependencies
  USAGE.md                # Detailed usage guide with examples
```
