"""Use Claude to resolve git conflicts with PR context."""

import logging
import re

import anthropic

from config import RebaseConfig
from git_ops import ConflictedFile
from pr_context import PRContext

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_FULL_FILE = """\
You are a git conflict resolution expert. Your job is to resolve cherry-pick \
conflicts by producing the correct merged file content.

We are cherry-picking internal-only commits onto the latest upstream code. \
The goal is to apply internal customizations on top of the current upstream state.

You will be given:
1. The file with conflict markers (<<<<<<< / ======= / >>>>>>>)
2. The "ours" version (current branch — based on latest upstream)
3. The "theirs" version (the internal commit being cherry-picked — contains custom changes)
4. The common base version
5. Context from past Pull Requests in the internal repo that modified this file

## Key Principles:
- **Preserve internal customizations**: The cherry-picked commit contains intentional \
internal changes. Past PRs explain WHY those changes were made. Apply their intent \
onto the current upstream code.
- **Keep upstream state as the foundation**: The upstream version is the base. Internal \
changes should be layered on top, not replace upstream improvements.
- **Use PR context as clues**: Past PRs tell you which parts of the file are \
intentionally different from upstream. Apply those intentional differences cleanly \
onto the current upstream code.
- **Maintain correctness**: The resolved file must be syntactically valid and \
logically coherent. No leftover conflict markers.

## Output format:
Return ONLY the fully resolved file content. No explanations, no markdown code \
fences, no commentary. Just the raw file content that should be written to disk.\
"""

SYSTEM_PROMPT_CHUNK = """\
You are a git conflict resolution expert. You will be given a single conflict \
block extracted from a file during a cherry-pick operation.

We are cherry-picking internal-only commits onto the latest upstream code. \
The goal is to apply internal customizations on top of the current upstream state.

## Key Principles:
- **Preserve internal customizations**: The "theirs" side contains intentional \
internal changes. Preserve their intent.
- **Keep upstream state as the foundation**: The "ours" side is the latest upstream. \
Internal changes should be layered on top.
- **Maintain correctness**: The resolved block must be syntactically valid and \
logically coherent.

## Output format:
Return ONLY the resolved code for this conflict block. No conflict markers, \
no explanations, no markdown code fences, no commentary. Just the raw resolved \
code that replaces the entire conflict block (from <<<<<<< to >>>>>>>).\
"""

# Regex to match a conflict block with surrounding context lines
CONFLICT_PATTERN = re.compile(
    r"(<<<<<<<[^\n]*\n)(.*?)(=======\n)(.*?)(>>>>>>>[^\n]*\n)",
    re.DOTALL,
)


def _extract_conflict_blocks(content: str) -> list[tuple[int, int, str, str, str]]:
    """
    Extract conflict blocks from a file.
    Returns list of (start_pos, end_pos, ours_text, theirs_text, full_block).
    """
    blocks = []
    for m in CONFLICT_PATTERN.finditer(content):
        start = m.start()
        end = m.end()
        ours_text = m.group(2)    # Between <<<<<<< and =======
        theirs_text = m.group(4)  # Between ======= and >>>>>>>
        full_block = m.group(0)
        blocks.append((start, end, ours_text, theirs_text, full_block))
    return blocks


def _get_surrounding_context(content: str, start: int, end: int, lines: int = 10) -> tuple[str, str]:
    """Get N lines of context before and after a conflict block."""
    before = content[:start].split("\n")
    after = content[end:].split("\n")
    ctx_before = "\n".join(before[-lines:]) if len(before) >= lines else "\n".join(before)
    ctx_after = "\n".join(after[:lines]) if len(after) >= lines else "\n".join(after)
    return ctx_before, ctx_after


def _build_chunk_prompt(
    filepath: str,
    block_idx: int,
    total_blocks: int,
    ours_text: str,
    theirs_text: str,
    ctx_before: str,
    ctx_after: str,
    pr_contexts: list[PRContext],
) -> str:
    """Build prompt for resolving a single conflict block."""
    parts = []
    parts.append(f"## File: `{filepath}` — Conflict block {block_idx}/{total_blocks}\n\n")

    parts.append("### Context before conflict:\n```\n")
    parts.append(ctx_before)
    parts.append("\n```\n\n")

    parts.append("### OURS (current upstream-based branch):\n```\n")
    parts.append(ours_text)
    parts.append("\n```\n\n")

    parts.append("### THEIRS (internal commit being cherry-picked):\n```\n")
    parts.append(theirs_text)
    parts.append("\n```\n\n")

    parts.append("### Context after conflict:\n```\n")
    parts.append(ctx_after)
    parts.append("\n```\n\n")

    if pr_contexts:
        parts.append("### Relevant past PRs (for understanding internal intent):\n")
        for pr in pr_contexts:
            parts.append(f"- PR #{pr.number}: {pr.title}\n")
            if pr.body:
                body_short = pr.body[:500]
                parts.append(f"  {body_short}\n")
        parts.append("\n")

    parts.append(
        "Resolve this conflict block. Output ONLY the resolved code that "
        "replaces the entire conflict. No markers, no fences, no commentary."
    )
    return "".join(parts)


def build_conflict_prompt(
    conflict: ConflictedFile, pr_contexts: list[PRContext]
) -> str:
    """Build the user prompt with all context for Claude (full-file mode)."""
    parts = []

    parts.append(f"## Conflicted file: `{conflict.path}`\n")

    parts.append("### File with conflict markers:\n```\n")
    parts.append(conflict.content_with_markers)
    parts.append("\n```\n")

    parts.append("### Ours (current branch — based on latest upstream):\n```\n")
    parts.append(conflict.ours)
    parts.append("\n```\n")

    parts.append("### Theirs (internal commit being cherry-picked):\n```\n")
    parts.append(conflict.theirs)
    parts.append("\n```\n")

    parts.append("### Common base version:\n```\n")
    parts.append(conflict.base)
    parts.append("\n```\n")

    if pr_contexts:
        parts.append("### Relevant past PRs from the internal repo:\n")
        parts.append(
            "These PRs previously modified this file. Use them to understand "
            "which changes are intentional internal customizations.\n\n"
        )
        for pr in pr_contexts:
            parts.append(f"#### PR #{pr.number}: {pr.title} (merged {pr.merged_at})\n")
            if pr.body:
                parts.append(f"Description: {pr.body}\n\n")
            parts.append(f"Diff for this file:\n```diff\n{pr.diff_for_file}\n```\n\n")
    else:
        parts.append(
            "### No past PR context available.\n"
            "Resolve based on the conflict markers and version diffs above.\n"
        )

    parts.append(
        "\nResolve this conflict now. Output ONLY the resolved file content."
    )
    return "".join(parts)


def _make_client(config: RebaseConfig) -> anthropic.AnthropicBedrock:
    bedrock_kwargs = {"aws_region": config.aws_region}
    if config.aws_access_key_id:
        bedrock_kwargs["aws_access_key"] = config.aws_access_key_id
    if config.aws_secret_access_key:
        bedrock_kwargs["aws_secret_key"] = config.aws_secret_access_key
    if config.aws_session_token:
        bedrock_kwargs["aws_session_token"] = config.aws_session_token
    return anthropic.AnthropicBedrock(**bedrock_kwargs)


def _has_conflict_markers(text: str) -> bool:
    return "<<<<<<" in text or ">>>>>>>" in text


def _resolve_chunk(
    client: anthropic.AnthropicBedrock,
    config: RebaseConfig,
    prompt: str,
    filepath: str,
    block_idx: int,
    max_retries: int = 3,
) -> str | None:
    """Resolve a single conflict chunk with retries."""
    for attempt in range(1, max_retries + 1):
        logger.info(
            "  Resolving block %d in %s (attempt %d/%d)",
            block_idx, filepath, attempt, max_retries,
        )
        try:
            messages = [{"role": "user", "content": prompt}]
            if attempt > 1:
                messages.append({"role": "assistant", "content": "Here is the resolved code:"})
                messages.append({
                    "role": "user",
                    "content": (
                        "Your previous attempt still contained conflict markers. "
                        "Output ONLY the resolved code. No markers, no fences."
                    ),
                })

            response = client.messages.create(
                model=config.claude_model,
                max_tokens=8000,
                system=SYSTEM_PROMPT_CHUNK,
                messages=messages,
            )
            if not response.content or not hasattr(response.content[0], "text"):
                logger.warning("  Empty response for block %d (attempt %d/%d)", block_idx, attempt, max_retries)
                if attempt < max_retries:
                    continue
                return None
            resolved = response.content[0].text

            if _has_conflict_markers(resolved):
                logger.warning(
                    "  Block %d still has markers (attempt %d/%d)",
                    block_idx, attempt, max_retries,
                )
                if attempt < max_retries:
                    continue
                return None
            return resolved

        except Exception as e:
            logger.error("  Claude API error for block %d: %s", block_idx, e)
            if attempt < max_retries:
                continue
            return None
    return None


def _resolve_full_file(
    client: anthropic.AnthropicBedrock,
    config: RebaseConfig,
    conflict: ConflictedFile,
    pr_contexts: list[PRContext],
    max_retries: int = 3,
) -> str | None:
    """Try resolving the entire file at once (for small files)."""
    prompt = build_conflict_prompt(conflict, pr_contexts)

    for attempt in range(1, max_retries + 1):
        logger.info(
            "Resolving full file: %s (attempt %d/%d)",
            conflict.path, attempt, max_retries,
        )
        try:
            messages = [{"role": "user", "content": prompt}]
            if attempt > 1:
                messages.append({"role": "assistant", "content": "I'll resolve this conflict now."})
                messages.append({
                    "role": "user",
                    "content": (
                        "Your previous attempt still contained conflict markers. "
                        "Output ONLY the final resolved file content. "
                        "No markers, no fences, no commentary."
                    ),
                })

            response = client.messages.create(
                model=config.claude_model,
                max_tokens=16000,
                system=SYSTEM_PROMPT_FULL_FILE,
                messages=messages,
            )
            if not response.content or not hasattr(response.content[0], "text"):
                logger.warning("Empty response for %s (attempt %d/%d)", conflict.path, attempt, max_retries)
                if attempt < max_retries:
                    continue
                return None
            resolved = response.content[0].text

            if _has_conflict_markers(resolved):
                logger.warning(
                    "Full-file resolution for %s still has markers (attempt %d/%d)",
                    conflict.path, attempt, max_retries,
                )
                if attempt < max_retries:
                    continue
                return None
            return resolved

        except Exception as e:
            logger.error("Claude API error resolving %s: %s", conflict.path, e)
            if attempt < max_retries:
                continue
            return None
    return None


# Threshold: if file content > this many chars, use chunk-based resolution
LARGE_FILE_THRESHOLD = 20_000


def resolve_conflict(
    config: RebaseConfig,
    conflict: ConflictedFile,
    pr_contexts: list[PRContext],
    max_retries: int = 3,
) -> str | None:
    """
    Resolve a conflicted file using Claude.

    For small files: sends the entire file for resolution.
    For large files: extracts individual conflict blocks, resolves each
    separately, and stitches the file back together.
    """
    client = _make_client(config)
    content = conflict.content_with_markers

    # Small file → full-file resolution
    if len(content) < LARGE_FILE_THRESHOLD:
        logger.info("Using full-file resolution for %s (%d chars)", conflict.path, len(content))
        return _resolve_full_file(client, config, conflict, pr_contexts, max_retries)

    # Large file → chunk-based resolution
    blocks = _extract_conflict_blocks(content)
    if not blocks:
        logger.warning("No conflict blocks found in %s despite markers", conflict.path)
        return _resolve_full_file(client, config, conflict, pr_contexts, max_retries)

    logger.info(
        "Using chunk-based resolution for %s (%d chars, %d conflict blocks)",
        conflict.path, len(content), len(blocks),
    )

    # Resolve each block and reconstruct the file
    resolved_content = content
    # Process blocks in reverse order so positions don't shift
    for idx, (start, end, ours_text, theirs_text, full_block) in enumerate(reversed(blocks)):
        block_num = len(blocks) - idx

        # Trivial cases: one side is empty (deletion vs addition)
        if not theirs_text.strip():
            # Internal commit deletes this section → use ours (upstream)
            logger.info("  Block %d: theirs is empty — keeping ours (upstream)", block_num)
            resolved_content = resolved_content[:start] + ours_text + resolved_content[end:]
            continue
        if not ours_text.strip():
            # Upstream deleted this section, internal adds → use theirs (internal)
            logger.info("  Block %d: ours is empty — keeping theirs (internal)", block_num)
            resolved_content = resolved_content[:start] + theirs_text + resolved_content[end:]
            continue

        ctx_before, ctx_after = _get_surrounding_context(resolved_content, start, end)

        prompt = _build_chunk_prompt(
            filepath=conflict.path,
            block_idx=block_num,
            total_blocks=len(blocks),
            ours_text=ours_text,
            theirs_text=theirs_text,
            ctx_before=ctx_before,
            ctx_after=ctx_after,
            pr_contexts=pr_contexts,
        )

        resolved_block = _resolve_chunk(
            client, config, prompt, conflict.path, block_num, max_retries,
        )

        if resolved_block is None:
            logger.error("Failed to resolve block %d in %s", block_num, conflict.path)
            return None

        # Replace the conflict block with resolved content
        resolved_content = resolved_content[:start] + resolved_block + resolved_content[end:]

    # Final sanity check
    if _has_conflict_markers(resolved_content):
        logger.error("Resolved content for %s still has markers after chunk resolution!", conflict.path)
        return None

    return resolved_content
