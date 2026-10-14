
"""Git operations. All shell out to the git CLI."""

import subprocess

from onset.models import Commit


class GitError(RuntimeError):
    pass


def _run(args, cwd=None, check=True):
    r = subprocess.run(args, capture_output=True, text=True, cwd=cwd)
    if check and r.returncode != 0:
        raise GitError("git " + " ".join(args[1:]) + " failed: " + r.stderr.strip()[:300])
    return r


def is_repo(path="."):
    r = _run(["git", "rev-parse", "--git-dir"], cwd=path, check=False)
    return r.returncode == 0


def is_clean(path="."):
    r = _run(["git", "status", "--porcelain"], cwd=path)
    return r.stdout.strip() == ""


def current_ref(path="."):
    r = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=path)
    ref = r.stdout.strip()
    if ref == "HEAD":
        # detached HEAD; get SHA
        r2 = _run(["git", "rev-parse", "HEAD"], cwd=path)
        return r2.stdout.strip()
    return ref


def resolve(ref, path="."):
    r = _run(["git", "rev-parse", ref], cwd=path)
    return r.stdout.strip()


def list_commits(start_ref, end_ref="HEAD", path="."):
    """Return commits from start_ref (exclusive) to end_ref (inclusive),
    oldest first."""
    fmt = "%H|%h|%an|%ad|%s"
    r = _run(
        ["git", "log", "--reverse",
         "--date=short",
         "--pretty=format:" + fmt,
         start_ref + ".." + end_ref],
        cwd=path,
    )
    commits = []
    for line in r.stdout.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        parts = line.split("|", 4)
        if len(parts) < 5:
            continue
        sha, short, author, date, message = parts
        commits.append(Commit(
            sha=sha, short=short, author=author, date=date, message=message,
        ))
    return commits


def commit_files(sha, path="."):
    r = _run(["git", "show", "--name-only", "--pretty=format:", sha], cwd=path)
    return [l.strip() for l in r.stdout.splitlines() if l.strip()]


def parent_of(sha, path="."):
    r = _run(["git", "rev-parse", sha + "^"], cwd=path)
    return r.stdout.strip()


def checkout(sha, path="."):
    _run(["git", "checkout", "--quiet", sha], cwd=path)


def restore(ref, path="."):
    _run(["git", "checkout", "--quiet", ref], cwd=path)
