"""Use Claude to resolve git conflicts with PR context."""

import logging
import re
from dataclasses import dataclass

import anthropic

from config import RebaseConfig
from git_ops import ConflictedFile
from pr_context import PRContext

logger = logging.getLogger(__name__)


@dataclass
class ResolutionResult:
    content: str
    confidence: int  # 0-100
    reasoning: str  # Brief explanation of confidence score

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
IMPORTANT: Do NOT include any reasoning, analysis, or explanation in your output. \
Do NOT wrap the code in markdown code fences (``` or ```python). \
Output the raw file content directly.

First, output the fully resolved file content — raw code only, starting from \
the very first line of the file (e.g. a comment, import, or [build-system]).
Then, on a NEW line after the LAST line of code, output exactly this marker \
followed by your confidence assessment:
---CONFIDENCE---
score: <0-100>
reasoning: <one sentence explaining your confidence level>

The score should reflect how confident you are that the resolution is correct:
- 90-100: Trivial or straightforward conflict (e.g. imports, simple additions)
- 70-89: Moderate complexity, high confidence the intent is preserved
- 50-69: Complex conflict, some ambiguity in the correct resolution
- 0-49: Significant uncertainty, manual review strongly recommended\
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
IMPORTANT: Do NOT include any reasoning, analysis, or explanation in your output. \
Do NOT wrap the code in markdown code fences (``` or ```python). \
Output the raw resolved code directly.

First, output the resolved code for this conflict block — raw code only, \
no conflict markers, no markdown.
Then, on a NEW line after the LAST line of code, output exactly this marker \
followed by your confidence assessment:
---CONFIDENCE---
score: <0-100>
reasoning: <one sentence explaining your confidence level>

The score should reflect how confident you are that the resolution is correct:
- 90-100: Trivial or straightforward conflict (e.g. imports, simple additions)
- 70-89: Moderate complexity, high confidence the intent is preserved
- 50-69: Complex conflict, some ambiguity in the correct resolution
- 0-49: Significant uncertainty, manual review strongly recommended\
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


CONFIDENCE_PATTERN = re.compile(
    r"---CONFIDENCE---\s*\n\s*score:\s*(\d+)\s*\n\s*reasoning:\s*(.+)",
    re.IGNORECASE,
)

# Pattern to match markdown code fences: ```python ... ``` or ``` ... ```
CODE_FENCE_PATTERN = re.compile(
    r"```[\w]*\s*\n(.*?)```",
    re.DOTALL,
)

# Lines that look like English prose reasoning (not code)
_PROSE_INDICATORS = re.compile(
    r"^(Looking at|However,|The OURS|The THEIRS|The upstream|The internal|"
    r"The conflict|The correct|The resolution|I'll keep|I should|I need to|"
    r"I preserved|I merged|I combined|I chose|Let me|Since |So the|For other|"
    r"Following the|This is |Both sides|The base|The cherry|The goal|"
    r"\d+\.\s+\*\*|   - )",
)


def _parse_confidence(text: str) -> tuple[str, int, str]:
    """
    Parse confidence marker from Claude's response.
    Returns (content_without_marker, score, reasoning).
    """
    m = CONFIDENCE_PATTERN.search(text)
    if m:
        score = min(100, max(0, int(m.group(1))))
        reasoning = m.group(2).strip()
        content = text[:m.start()].rstrip()
        return content, score, reasoning
    # No marker found — return full text with default unknown confidence
    return text, -1, "no confidence score returned"


def _strip_code_fences(text: str) -> str:
    """
    If the response is wrapped in markdown code fences, extract just the content.
    Handles ```python ... ``` and ``` ... ```.
    """
    matches = list(CODE_FENCE_PATTERN.finditer(text))
    if not matches:
        return text

    # If there's exactly one fenced block that covers most of the text,
    # it's the whole response wrapped in fences — extract it
    if len(matches) == 1:
        inner = matches[0].group(1)
        # Check that the fenced block is the bulk of the content
        # (not just a small example inside reasoning)
        outer_text = text[:matches[0].start()] + text[matches[0].end():]
        if len(inner.strip()) > len(outer_text.strip()):
            return inner

    # Multiple fence blocks or fence is a small part — could be
    # reasoning with code examples. Extract and concatenate all fenced blocks.
    # But only if the non-fenced text looks like prose.
    non_fenced = text
    for m in reversed(matches):
        non_fenced = non_fenced[:m.start()] + non_fenced[m.end():]
    non_fenced_lines = [l for l in non_fenced.strip().splitlines() if l.strip()]
    if non_fenced_lines and all(
        _PROSE_INDICATORS.match(l.strip()) or not l.strip()
        for l in non_fenced_lines[:5]
    ):
        # Non-fenced content is reasoning — return only the fenced code
        return "\n".join(m.group(1) for m in matches)

    return text


def _strip_preamble(text: str) -> str:
    """
    Remove any reasoning/analysis text that appears before the actual code.
    Detects prose lines at the start of the response and strips them.
    """
    lines = text.split("\n")
    first_code_line = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        # If line looks like prose reasoning, skip it
        if _PROSE_INDICATORS.match(stripped):
            first_code_line = i + 1
            continue
        # Markdown-style lines (bullet points, numbered lists, bold)
        if stripped.startswith(("- ", "* ", "**")):
            first_code_line = i + 1
            continue
        # Blank lines between prose are also preamble
        if first_code_line > 0 and not stripped:
            first_code_line = i + 1
            continue
        # Found a non-prose line — stop
        break

    if first_code_line > 0:
        # Skip any remaining blank lines after the preamble
        while first_code_line < len(lines) and not lines[first_code_line].strip():
            first_code_line += 1
        return "\n".join(lines[first_code_line:])

    return text


def _clean_response(text: str) -> tuple[str, int, str]:
    """
    Clean Claude's response by:
    1. Parsing and stripping the ---CONFIDENCE--- marker
    2. Stripping markdown code fences
    3. Stripping preamble reasoning text

    Returns (clean_content, confidence_score, reasoning).
    """
    # Step 1: Parse confidence (removes everything after ---CONFIDENCE---)
    content, score, reasoning = _parse_confidence(text)

    # Step 2: Strip code fences
    content = _strip_code_fences(content)

    # Step 3: Strip preamble reasoning
    content = _strip_preamble(content)

    # Step 4: Strip trailing whitespace/fences
    content = content.rstrip()
    if content.endswith("```"):
        content = content[:-3].rstrip()

    return content, score, reasoning


def _has_conflict_markers(text: str) -> bool:
    return "<<<<<<" in text or ">>>>>>>" in text


def _resolve_chunk(
    client: anthropic.AnthropicBedrock,
    config: RebaseConfig,
    prompt: str,
    filepath: str,
    block_idx: int,
    max_retries: int = 3,
) -> ResolutionResult | None:
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
            raw = response.content[0].text
            resolved, confidence, reasoning = _clean_response(raw)

            if _has_conflict_markers(resolved):
                logger.warning(
                    "  Block %d still has markers (attempt %d/%d)",
                    block_idx, attempt, max_retries,
                )
                if attempt < max_retries:
                    continue
                return None

            logger.info(
                "  Block %d confidence: %d%% — %s",
                block_idx, confidence, reasoning,
            )
            return ResolutionResult(content=resolved, confidence=confidence, reasoning=reasoning)

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
) -> ResolutionResult | None:
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
            raw = response.content[0].text
            resolved, confidence, reasoning = _clean_response(raw)

            if _has_conflict_markers(resolved):
                logger.warning(
                    "Full-file resolution for %s still has markers (attempt %d/%d)",
                    conflict.path, attempt, max_retries,
                )
                if attempt < max_retries:
                    continue
                return None

            logger.info(
                "  Confidence for %s: %d%% — %s",
                conflict.path, confidence, reasoning,
            )
            return ResolutionResult(content=resolved, confidence=confidence, reasoning=reasoning)

        except Exception as e:
            logger.error("Claude API error resolving %s: %s", conflict.path, e)
            if attempt < max_retries:
                continue
            return None
    return None


# Threshold: if file content > this many chars, use chunk-based resolution
LARGE_FILE_THRESHOLD = 40_000


def resolve_conflict(
    config: RebaseConfig,
    conflict: ConflictedFile,
    pr_contexts: list[PRContext],
    max_retries: int = 3,
) -> ResolutionResult | None:
    """
    Resolve a conflicted file using Claude.

    For small files: sends the entire file for resolution.
    For large files: extracts individual conflict blocks, resolves each
    separately, and stitches the file back together.

    Returns ResolutionResult with content, confidence score, and reasoning.
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
    block_confidences: list[int] = []
    block_reasonings: list[str] = []

    # Process blocks in reverse order so positions don't shift
    for idx, (start, end, ours_text, theirs_text, full_block) in enumerate(reversed(blocks)):
        block_num = len(blocks) - idx

        # Trivial cases: one side is empty (deletion vs addition)
        if not theirs_text.strip():
            # Internal commit deletes this section → use ours (upstream)
            logger.info("  Block %d: theirs is empty — keeping ours (upstream)", block_num)
            resolved_content = resolved_content[:start] + ours_text + resolved_content[end:]
            block_confidences.append(100)
            block_reasonings.append("trivial: one side empty")
            continue
        if not ours_text.strip():
            # Upstream deleted this section, internal adds → use theirs (internal)
            logger.info("  Block %d: ours is empty — keeping theirs (internal)", block_num)
            resolved_content = resolved_content[:start] + theirs_text + resolved_content[end:]
            block_confidences.append(100)
            block_reasonings.append("trivial: one side empty")
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

        result = _resolve_chunk(
            client, config, prompt, conflict.path, block_num, max_retries,
        )

        if result is None:
            logger.error("Failed to resolve block %d in %s", block_num, conflict.path)
            return None

        # Replace the conflict block with resolved content
        resolved_content = resolved_content[:start] + result.content + resolved_content[end:]
        block_confidences.append(result.confidence)
        block_reasonings.append(result.reasoning)

    # Final sanity check
    if _has_conflict_markers(resolved_content):
        logger.error("Resolved content for %s still has markers after chunk resolution!", conflict.path)
        return None

    # Aggregate confidence: use minimum across all blocks (weakest link)
    valid_scores = [s for s in block_confidences if s >= 0]
    avg_confidence = min(valid_scores) if valid_scores else -1
    summary = f"min of {len(blocks)} blocks; lowest: {min(valid_scores)}%"  if valid_scores else "no scores"

    logger.info(
        "  Overall confidence for %s: %d%% (%s)",
        conflict.path, avg_confidence, summary,
    )

    return ResolutionResult(
        content=resolved_content,
        confidence=avg_confidence,
        reasoning=summary,
    )
