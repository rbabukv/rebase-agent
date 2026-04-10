"""Git operations for the rebase agent."""

import logging
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from config import RebaseConfig

logger = logging.getLogger(__name__)


@dataclass
class ConflictedFile:
    path: str
    content_with_markers: str  # Full file content with conflict markers
    ours: str  # Our version (the new branch, based on upstream)
    theirs: str  # Their version (from the cherry-picked internal commit)
    base: str  # Common ancestor version


@dataclass
class InternalCommit:
    sha: str
    subject: str  # First line of commit message
    message: str  # Full commit message


@dataclass
class UpstreamCommit:
    sha: str
    subject: str  # First line of commit message


class GitOperations:
    def __init__(self, config: RebaseConfig):
        self.config = config
        if config.work_dir:
            self.work_dir = Path(config.work_dir).resolve()
            self.work_dir.mkdir(parents=True, exist_ok=True)
            self._tmp = None
        else:
            self._tmp = tempfile.TemporaryDirectory(prefix="rebase-agent-")
            self.work_dir = Path(self._tmp.name)
        self.repo_dir: Path | None = None

    def cleanup(self):
        if self._tmp:
            self._tmp.cleanup()

    def _run(self, *args: str, cwd: Path | None = None,
             env: dict | None = None) -> subprocess.CompletedProcess:
        cwd = cwd or self.repo_dir
        cmd = ["git"] + list(args)
        logger.debug("Running: %s (cwd=%s)", " ".join(cmd), cwd)
        import os
        run_env = None
        if env:
            run_env = os.environ.copy()
            run_env.update(env)
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=300,
            env=run_env,
        )
        if result.returncode != 0:
            logger.debug("stderr: %s", result.stderr)
        return result

    def clone_internal(self) -> Path:
        """Clone the internal repo into the work directory."""
        self.repo_dir = self.work_dir / "repo"
        if self.repo_dir.exists():
            logger.info("Repo already exists at %s, fetching instead", self.repo_dir)
            self._run("fetch", "origin")
            self._run("checkout", self.config.internal_branch)
            self._run("reset", "--hard", f"origin/{self.config.internal_branch}")
        else:
            logger.info("Cloning %s", self.config.internal_repo_url)
            result = self._run(
                "clone", self.config.internal_repo_url, str(self.repo_dir),
                cwd=self.work_dir,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Clone failed: {result.stderr}")
            self._run("checkout", self.config.internal_branch)
        return self.repo_dir

    def add_upstream_remote(self):
        """Add upstream as a remote if not already present."""
        result = self._run("remote", "get-url", "upstream")
        if result.returncode != 0:
            logger.info("Adding upstream remote: %s", self.config.upstream_repo_url)
            self._run("remote", "add", "upstream", self.config.upstream_repo_url)
        self._run("fetch", "upstream")

    def _upstream_ref(self) -> str:
        """Return the upstream ref to use as base — specific commit/tag or branch HEAD."""
        if self.config.upstream_base:
            return self.config.upstream_base
        return f"upstream/{self.config.upstream_branch}"

    def get_internal_only_commits(self) -> list[InternalCommit]:
        """
        Find commits in the internal branch that are NOT in upstream.
        Returns them in chronological order (oldest first) for cherry-picking.

        If internal_start is set, only returns commits from that SHA (inclusive)
        through the internal branch HEAD.
        """
        if self.config.internal_start:
            # Cherry-pick from the specified commit (inclusive) to branch HEAD
            # <commit>^..HEAD gives us the commit itself plus everything after it
            result = self._run(
                "log", "--reverse", "--no-merges", "--format=%H%n%s%n%B%n---END---",
                f"{self.config.internal_start}^..origin/{self.config.internal_branch}",
            )
        else:
            upstream_ref = self._upstream_ref()
            # Commits in internal that are not in upstream (reverse = oldest first)
            result = self._run(
                "log", "--reverse", "--no-merges", "--format=%H%n%s%n%B%n---END---",
                f"{upstream_ref}..origin/{self.config.internal_branch}",
            )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to find internal-only commits: {result.stderr}")

        commits = []
        raw_commits = result.stdout.split("---END---\n")
        for block in raw_commits:
            block = block.strip()
            if not block:
                continue
            lines = block.split("\n", 2)
            if len(lines) < 2:
                continue
            sha = lines[0].strip()
            subject = lines[1].strip()
            message = lines[2].strip() if len(lines) > 2 else subject
            commits.append(InternalCommit(sha=sha, subject=subject, message=message))

        logger.info(
            "Found %d internal-only commits to cherry-pick", len(commits)
        )
        return commits

    def create_branch_from_upstream(self) -> str:
        """Create a new branch starting from upstream base. Returns branch name."""
        upstream_ref = self._upstream_ref()
        upstream_sha = self._get_short_sha(upstream_ref)
        local_sha = self._get_short_sha(f"origin/{self.config.internal_branch}")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        branch_name = f"rebase_{timestamp}_{upstream_sha}_{local_sha}"

        result = self._run(
            "checkout", "-b", branch_name,
            upstream_ref,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to create branch from upstream: {result.stderr}"
            )
        logger.info("Created branch '%s' from %s", branch_name, upstream_ref)
        return branch_name

    def cherry_pick(self, commit: InternalCommit) -> bool | None:
        """
        Cherry-pick a single commit.
        Returns True if clean, False if conflicts, None if empty (already in upstream).
        """
        logger.info("Cherry-picking %s: %s", commit.sha[:8], commit.subject)
        result = self._run("cherry-pick", commit.sha)
        if result.returncode == 0:
            return True
        # Check if cherry-pick resulted in an empty commit (already in upstream)
        if "empty" in result.stderr.lower():
            logger.info("Skipping %s — already in upstream (empty cherry-pick).", commit.sha[:8])
            self._run("cherry-pick", "--skip")
            return None
        # Check if it's a conflict vs some other error
        check = self._run("diff", "--name-only", "--diff-filter=U")
        if check.stdout.strip():
            logger.info("Cherry-pick has conflicts.")
            return False
        raise RuntimeError(
            f"Cherry-pick failed (not a conflict): {result.stderr}"
        )

    def get_conflicted_files(self) -> list[ConflictedFile]:
        """Parse conflicted files during an active cherry-pick."""
        result = self._run("diff", "--name-only", "--diff-filter=U")
        if result.returncode != 0:
            return []

        conflicted = []
        for filepath in result.stdout.strip().splitlines():
            filepath = filepath.strip()
            if not filepath:
                continue

            full_path = self.repo_dir / filepath
            if not full_path.exists():
                continue

            content = full_path.read_text(errors="replace")

            # During cherry-pick:
            # :2: = ours (the branch we're on, i.e. upstream-based)
            # :3: = theirs (the commit being cherry-picked, i.e. internal)
            # :1: = base (common ancestor)
            ours = self._run("show", f":2:{filepath}").stdout
            theirs = self._run("show", f":3:{filepath}").stdout
            base = self._run("show", f":1:{filepath}").stdout

            conflicted.append(ConflictedFile(
                path=filepath,
                content_with_markers=content,
                ours=ours,
                theirs=theirs,
                base=base,
            ))

        return conflicted

    def apply_resolution(self, filepath: str, resolved_content: str):
        """Write resolved content and mark file as resolved."""
        full_path = self.repo_dir / filepath
        full_path.write_text(resolved_content)
        self._run("add", filepath)

    def continue_cherry_pick(
        self, original_commit: InternalCommit, resolved_files: list[str] | None = None
    ) -> bool:
        """Continue cherry-pick after resolving conflicts. Returns True if done."""
        # Build the commit message
        if resolved_files:
            file_list = ", ".join(resolved_files)
            msg = (
                f"[Conflict resolved] {original_commit.message.rstrip()}\n\n"
                f"Conflict resolved by rebase-agent in: {file_list}"
            )
        else:
            msg = original_commit.message

        # Use GIT_EDITOR=true to skip editor, commit with our message
        result = self._run(
            "commit", "--allow-empty-message", "-m", msg,
        )
        # If cherry-pick already committed (no conflicts case), this may fail
        if result.returncode != 0:
            # Try continuing the cherry-pick instead
            result = self._run(
                "cherry-pick", "--continue",
                env={"GIT_EDITOR": "true"},
            )
        return result.returncode == 0

    def abort_cherry_pick(self):
        """Abort the current cherry-pick."""
        self._run("cherry-pick", "--abort")

    def _get_short_sha(self, ref: str) -> str:
        """Get the short commit SHA for a ref."""
        result = self._run("rev-parse", "--short=8", ref)
        if result.returncode != 0:
            return "unknown"
        return result.stdout.strip()

    def get_head_sha(self) -> str:
        """Get the full SHA of the current HEAD commit."""
        result = self._run("rev-parse", "HEAD")
        if result.returncode != 0:
            return "unknown"
        return result.stdout.strip()

    def push_result(self, branch_name: str, force: bool = False):
        """Push the branch to internal remote."""
        args = ["push", "origin", branch_name]
        if force:
            args.insert(1, "--force-with-lease")
        result = self._run(*args)
        if result.returncode != 0:
            raise RuntimeError(f"Push failed: {result.stderr}")
        logger.info("Pushed branch to origin/%s", branch_name)

    def get_file_log(self, filepath: str, max_commits: int = 20) -> str:
        """Get recent commit log for a specific file (internal repo)."""
        result = self._run(
            "log", f"--max-count={max_commits}", "--oneline",
            f"origin/{self.config.internal_branch}", "--", filepath,
        )
        return result.stdout.strip()

    def get_upstream_commit_subjects(self, since_days: int = 365) -> list[UpstreamCommit]:
        """Get upstream commit subjects from the last `since_days` days for similarity matching."""
        upstream_ref = self._upstream_ref()
        result = self._run(
            "log", f"--since={since_days} days ago", "--no-merges",
            "--format=%H %s", upstream_ref,
        )
        if result.returncode != 0:
            logger.warning("Failed to get upstream commits: %s", result.stderr)
            return []

        commits = []
        for line in result.stdout.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(" ", 1)
            if len(parts) == 2:
                commits.append(UpstreamCommit(sha=parts[0], subject=parts[1]))

        logger.info("Fetched %d upstream commit subjects (last %d days)", len(commits), since_days)
        return commits

    def get_branch_name(self) -> str:
        """Get the current branch name."""
        result = self._run("rev-parse", "--abbrev-ref", "HEAD")
        return result.stdout.strip()
