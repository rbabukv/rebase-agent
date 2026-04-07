import os
from dataclasses import dataclass, field


@dataclass
class RebaseConfig:
    # Git remotes
    internal_repo_url: str
    upstream_repo_url: str

    # Branch names
    internal_branch: str = "main"
    upstream_branch: str = "main"

    # GitHub settings (for PR context fetching)
    # Format: "owner/repo" e.g. "myorg/myrepo"
    github_internal_repo: str = ""

    # API keys (fall back to env vars)
    github_token: str = ""

    # AWS Bedrock settings
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_session_token: str = ""

    # How many past PRs to search per conflicted file
    max_prs_per_file: int = 10

    # Specific internal commit SHA to start cherry-picking from (inclusive, through branch HEAD)
    internal_start: str = ""

    # Specific upstream commit or tag to use as rebase base (default: upstream branch HEAD)
    upstream_base: str = ""

    # Working directory for clone (temp dir if empty)
    work_dir: str = ""

    # Claude model to use for conflict resolution (Bedrock model ID)
    claude_model: str = "us.anthropic.claude-opus-4-6-v1"

    # Microsoft Teams Incoming Webhook URL for notifications
    teams_webhook_url: str = ""

    def __post_init__(self):
        if not self.github_token:
            self.github_token = os.environ.get("GITHUB_TOKEN", "")
        if not self.aws_region:
            self.aws_region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
        if not self.aws_access_key_id:
            self.aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID", "")
        if not self.aws_secret_access_key:
            self.aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
        if not self.aws_session_token:
            self.aws_session_token = os.environ.get("AWS_SESSION_TOKEN", "")
        if not self.teams_webhook_url:
            self.teams_webhook_url = os.environ.get("TEAMS_WEBHOOK_URL", "")
        if not self.github_internal_repo and self.internal_repo_url:
            # Try to extract owner/repo from URL
            url = self.internal_repo_url.rstrip("/").removesuffix(".git")
            parts = url.split("/")
            if len(parts) >= 2:
                self.github_internal_repo = f"{parts[-2]}/{parts[-1]}"
