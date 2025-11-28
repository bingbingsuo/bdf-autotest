"""
Git integration utilities
"""

from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import logging

from git import Repo, GitCommandError, InvalidGitRepositoryError  # type: ignore


class GitManager:
    """Manage cloning and pulling the package repository"""

    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        git_cfg = config.get("git", {})
        self.remote_url = git_cfg.get("remote_url")
        self.branch = git_cfg.get("branch", "master")
        self.local_path = Path(git_cfg.get("local_path", "./package_source")).resolve()
        self.logger = logger or logging.getLogger("bdf_autotest.git")
        self.repo: Optional[Repo] = None

    def ensure_repo(self) -> Repo:
        """Clone repository if missing, otherwise open existing repo"""
        if self.repo:
            return self.repo

        repo_exists = (self.local_path / ".git").exists()
        if repo_exists:
            try:
                self.repo = Repo(self.local_path)
                self.logger.debug("Opened existing repository at %s", self.local_path)
            except InvalidGitRepositoryError:
                self.logger.error("Directory exists but is not a git repository: %s", self.local_path)
                raise
        else:
            self.logger.info("Cloning repository from %s to %s", self.remote_url, self.local_path)
            self.local_path.parent.mkdir(parents=True, exist_ok=True)
            self.repo = Repo.clone_from(self.remote_url, self.local_path, branch=self.branch)

        return self.repo

    def sync(self) -> Tuple[str, str]:
        """
        Pull latest changes from remote.
        Returns tuple of (old_commit, new_commit)
        """
        repo = self.ensure_repo()
        old_commit = repo.head.commit.hexsha if repo.head.is_valid() else ""

        try:
            self.logger.info("Fetching latest changes for branch %s", self.branch)
            repo.remotes.origin.fetch()
            self.logger.info("Pulling latest changes")
            repo.remotes.origin.pull(self.branch)
        except GitCommandError as exc:
            self.logger.error("Git pull failed: %s", exc)
            raise

        new_commit = repo.head.commit.hexsha if repo.head.is_valid() else ""
        if old_commit != new_commit:
            self.logger.info("Repository updated: %s -> %s", old_commit[:7], new_commit[:7])
        else:
            self.logger.info("Repository already up-to-date at %s", new_commit[:7])
        return old_commit, new_commit

    def get_status(self) -> str:
        """Return short status of working tree"""
        repo = self.ensure_repo()
        status_lines = []
        if repo.is_dirty(untracked_files=True):
            status_lines.append("Working tree has local changes.")
        else:
            status_lines.append("Working tree clean.")
        status_lines.append(f"Current branch: {repo.active_branch}")
        status_lines.append(f"HEAD: {repo.head.commit.hexsha[:7]} - {repo.head.commit.summary}")
        return " ".join(status_lines)

