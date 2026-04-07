# Rebase Agent — Usage Guide

AI-powered tool that applies internal-only commits on top of the latest upstream code using cherry-pick. Produces a clean linear history — no merge commits, no rebase commits. Uses Claude to automatically resolve conflicts by learning from past PR history.

## Prerequisites

```bash
pip install -r requirements.txt
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `AWS_REGION` | No | AWS region for Bedrock (default: `us-east-1`) |
| `AWS_ACCESS_KEY_ID` | No* | AWS access key ID |
| `AWS_SECRET_ACCESS_KEY` | No* | AWS secret access key |
| `AWS_SESSION_TOKEN` | No | AWS session token (for temporary credentials) |
| `GITHUB_TOKEN` | Yes | GitHub personal access token (for fetching PR context) |
| `TEAMS_WEBHOOK_URL` | No | Microsoft Teams Incoming Webhook URL for notifications |

\* AWS credentials can come from environment variables, `~/.aws/credentials`, an IAM instance role, or SSO profile. If already configured via AWS CLI (`aws configure` or `aws sso login`), no env vars are needed.

## Basic Usage

```bash
export GITHUB_TOKEN="ghp_..."

# If AWS credentials aren't already configured:
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="us-east-1"

python agent.py \
    --internal git@github.com:your-org/internal-repo.git \
    --upstream git@github.com:upstream-org/upstream-repo.git \
    --github-repo your-org/internal-repo
```

## All Options

| Option | Default | Description |
|---|---|---|
| `--internal` | *(required)* | Internal repo URL |
| `--upstream` | *(required)* | Upstream repo URL |
| `--internal-branch` | `main` | Internal branch name |
| `--internal-start` | *(auto-detect)* | Internal commit SHA to start cherry-picking from (inclusive, through branch HEAD) |
| `--upstream-branch` | `main` | Upstream branch name |
| `--upstream-base` | *(branch HEAD)* | Specific upstream commit SHA or tag to use as rebase base |
| `--github-repo` | *(auto-detected)* | GitHub repo for PR context (`owner/repo`) |
| `--push` | `false` | Push result branch to remote after success |
| `--work-dir` | *(temp dir)* | Working directory for clone |
| `--model` | `us.anthropic.claude-sonnet-4-6-20250514-v1:0` | Bedrock model ID |
| `--aws-region` | `us-east-1` | AWS region for Bedrock |
| `--max-prs` | `10` | Max past PRs to fetch per conflicted file |
| `--teams-webhook` | *(none)* | Microsoft Teams Incoming Webhook URL |
| `-v, --verbose` | `false` | Enable debug logging |

## Examples

### Apply internal commits onto upstream (local only)

```bash
python agent.py \
    --internal git@github.com:your-org/internal-repo.git \
    --upstream git@github.com:upstream-org/upstream-repo.git \
    --work-dir ./rebase-workspace \
    -v
```

### With Teams notifications and push

```bash
python agent.py \
    --internal git@github.com:your-org/internal-repo.git \
    --upstream git@github.com:upstream-org/upstream-repo.git \
    --teams-webhook "https://your-org.webhook.office.com/webhookb2/..." \
    --push
```

### Custom branches

```bash
python agent.py \
    --internal git@github.com:your-org/internal-repo.git \
    --upstream git@github.com:upstream-org/upstream-repo.git \
    --internal-branch master_next \
    --upstream-branch main
```

### Cherry-pick from a specific internal commit

```bash
# Cherry-pick commits from a1b2c3d4 (inclusive) through internal branch HEAD
python agent.py \
    --internal git@github.com:your-org/internal-repo.git \
    --upstream git@github.com:upstream-org/upstream-repo.git \
    --internal-start a1b2c3d4
```

### Rebase onto a specific upstream commit or tag

```bash
python agent.py \
    --internal git@github.com:your-org/internal-repo.git \
    --upstream git@github.com:upstream-org/upstream-repo.git \
    --upstream-base v2.5.0

# Or using a specific commit SHA:
python agent.py \
    --internal git@github.com:your-org/internal-repo.git \
    --upstream git@github.com:upstream-org/upstream-repo.git \
    --upstream-base a1b2c3d4e5f6
```

## How It Works

1. **Clones the internal repo** and adds upstream as a remote.
2. **Finds internal-only commits** — commits in the internal branch that are not in upstream (excludes merge commits).
3. **Creates a new branch** from `upstream/<branch>` HEAD, named `rebase_<timestamp>_<upstream SHA>_<local SHA>`.
4. **Cherry-picks each internal commit** one by one onto the new branch.
5. When a cherry-pick has conflicts, for each conflicted file:
   - Extracts three versions: **ours** (upstream-based branch), **theirs** (internal commit being cherry-picked), and **base** (common ancestor).
   - Fetches merged PRs from the internal repo that previously modified the same file.
   - Sends all context to Claude, which resolves the conflict — applying internal customizations cleanly on top of the latest upstream code.
6. **Tags resolved commits** — prepends `[Conflict resolved]` to the commit message.
7. **Scores confidence** — each resolved file gets a confidence score (0–100%) indicating how certain Claude is about the resolution.
8. **Result**: a clean linear branch with no merge or rebase commits.
9. Prints a **confidence summary** and flags files below 70% for manual review.
10. Sends a Teams notification with the result (including confidence scores).

## Branch Naming

The result branch follows the format:

```
rebase_<timestamp>_<upstream_top_commit>_<local_top_commit>
```

For example:

```
rebase_20260406143022_a1b2c3d4_e5f6g7h8
```

| Component | Description |
|---|---|
| `timestamp` | UTC timestamp of the run (`YYYYMMDDHHMMSS`) |
| `upstream_top_commit` | Short SHA (8 chars) of the upstream branch HEAD |
| `local_top_commit` | Short SHA (8 chars) of the internal branch HEAD |

This allows you to review the result on a separate branch before merging.

## Identifying Resolved Commits

Any commit where the agent resolved conflicts will have its message updated:

```
[Conflict resolved] Original commit message here

Conflict resolved by rebase-agent in: path/to/file1.py, path/to/file2.py
```

Use `git log --grep="Conflict resolved"` to find all auto-resolved commits for review.

## Confidence Scores

After resolving conflicts, the agent prints a confidence summary for every resolved file:

```
=== Conflict Resolution Confidence Summary ===
File                                               Commit     Score  Reasoning
--------------------------------------------------------------------------------------------------------------
python/sglang/srt/layers/rotary_embedding.py       a1b2c3d4   62%    complex logic merge with ambiguous intent
python/pyproject_xpu.toml                           e5f6g7h8   85%    straightforward dependency version update
test/registered/unit/test_swa_unittest.py           d0eec661   95%    trivial device-agnostic change
--------------------------------------------------------------------------------------------------------------
Average confidence: 81% | Files resolved: 3 | Needs review (< 70%): 1
```

| Score | Meaning |
|---|---|
| 90–100% | Trivial or straightforward conflict (e.g. imports, simple additions) |
| 70–89% | Moderate complexity, high confidence the intent is preserved |
| 50–69% | Complex conflict, some ambiguity — review recommended |
| 0–49% | Significant uncertainty — manual review strongly recommended |

Files scoring below 70% are flagged in both the console output and the Teams notification.

## Teams Webhook Setup

1. In your Teams channel, click **...** > **Manage channel** > **Connectors** (or **Workflows** for newer Teams).
2. Add an **Incoming Webhook**, name it (e.g., "Rebase Agent"), and copy the URL.
3. Pass the URL via `--teams-webhook` or `TEAMS_WEBHOOK_URL` environment variable.

## Project Structure

```
rebase-agent/
  agent.py              — Main orchestrator and CLI entry point
  config.py             — Configuration dataclass
  git_ops.py            — Git operations (clone, cherry-pick, conflict detection)
  pr_context.py         — Fetches past PR context from GitHub
  conflict_resolver.py  — Claude-powered conflict resolution
  notifier.py           — Microsoft Teams notifications
  requirements.txt      — Python dependencies
```
