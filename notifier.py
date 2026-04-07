"""Microsoft Teams notifications for the rebase agent."""

import json
import logging
import urllib.request
import urllib.error
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceEntry:
    path: str
    commit_sha: str
    confidence: int
    reasoning: str


@dataclass
class RebaseResult:
    success: bool
    internal_repo: str
    upstream_repo: str
    internal_branch: str
    upstream_branch: str
    conflicts_resolved: list[str]  # List of file paths that had conflicts
    confidence_scores: list[ConfidenceEntry] | None = None
    failed_file: str | None = None  # File that couldn't be resolved
    error_message: str | None = None
    push_branch: str | None = None  # Branch name the result was pushed to


def _build_card(result: RebaseResult) -> dict:
    """Build an Adaptive Card payload for Teams."""
    color = "Good" if result.success else "Attention"
    status = "Rebase Succeeded" if result.success else "Rebase Failed"

    facts = [
        {"title": "Internal Repo", "value": result.internal_repo},
        {"title": "Upstream Repo", "value": result.upstream_repo},
        {"title": "Branches", "value": f"{result.internal_branch} <- {result.upstream_branch}"},
        {"title": "Conflicts Resolved", "value": str(len(result.conflicts_resolved))},
    ]

    if result.push_branch:
        facts.append({"title": "Pushed To", "value": f"`{result.push_branch}`"})

    if result.conflicts_resolved:
        file_list = ", ".join(f"`{f}`" for f in result.conflicts_resolved)
        facts.append({"title": "Resolved Files", "value": file_list})

    if result.confidence_scores:
        valid = [s.confidence for s in result.confidence_scores if s.confidence >= 0]
        if valid:
            avg = sum(valid) / len(valid)
            low_count = sum(1 for s in valid if s < 70)
            facts.append({"title": "Avg Confidence", "value": f"{avg:.0f}%"})
            if low_count:
                low_files = [
                    f"`{s.path}` ({s.confidence}%)"
                    for s in result.confidence_scores if 0 <= s.confidence < 70
                ]
                facts.append({"title": "Needs Review", "value": ", ".join(low_files)})

    if result.failed_file:
        facts.append({"title": "Failed On", "value": f"`{result.failed_file}`"})

    if result.error_message:
        facts.append({"title": "Error", "value": result.error_message})

    # Adaptive Card format (works with Teams Workflows and Incoming Webhooks)
    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {
                            "type": "TextBlock",
                            "size": "Medium",
                            "weight": "Bolder",
                            "text": status,
                            "color": color,
                        },
                        {
                            "type": "FactSet",
                            "facts": [
                                {"title": f["title"], "value": f["value"]}
                                for f in facts
                            ],
                        },
                    ],
                },
            }
        ],
    }


def send_teams_notification(webhook_url: str, result: RebaseResult):
    """Send a notification to Microsoft Teams via Incoming Webhook."""
    if not webhook_url:
        logger.warning("No Teams webhook URL configured — skipping notification")
        return

    payload = _build_card(result)
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            logger.info("Teams notification sent (status %d)", resp.status)
    except urllib.error.HTTPError as e:
        logger.error("Teams webhook HTTP error %d: %s", e.code, e.read().decode())
    except Exception as e:
        logger.error("Failed to send Teams notification: %s", e)
