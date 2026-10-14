
"""Bisection engine for onset.

Given a test that's flaky at HEAD and (assumed) not flaky at a good ref,
binary-search the commits between them to find the crossing point.
Then verify statistically before reporting a culprit.
"""

import os

from dotenv import load_dotenv

from onset import git
from onset.models import Finding
from onset.runner import run_n
from onset.stats import two_proportion_p_value

load_dotenv()


def _config():
    return {
        "min_flake_rate": float(os.getenv("ONSET_MIN_FLAKE_RATE", "0.05")),
        "min_runs": int(os.getenv("ONSET_MIN_RUNS", "10")),
        "p_threshold": float(os.getenv("ONSET_P_THRESHOLD", "0.05")),
    }


def find_onset(test_id, good_ref, runs=None, cwd=".", verbose=True):
    """Find the commit that made test_id flaky."""
    cfg = _config()
    runs = runs or cfg["min_runs"]

    if not git.is_repo(cwd):
        return Finding(test_id=test_id, status="error",
                       message="not a git repository: " + cwd)

    if not git.is_clean(cwd):
        return Finding(test_id=test_id, status="error",
                       message="working tree is not clean. Commit or stash first.")

    original_ref = git.current_ref(cwd)

    try:
        return _find_onset_inner(test_id, good_ref, runs, cfg, cwd, verbose)
    finally:
        if verbose:
            print("  restoring " + original_ref)
        git.restore(original_ref, cwd)


def _find_onset_inner(test_id, good_ref, runs, cfg, cwd, verbose):
    commits = git.list_commits(good_ref, "HEAD", cwd)
    if not commits:
        return Finding(test_id=test_id, status="error",
                       message="no commits between " + good_ref + " and HEAD")

    if verbose:
        print("Commits between " + good_ref + " and HEAD: " + str(len(commits)))
        print("Runs per commit: " + str(runs))
        print("Min flake rate: " + str(cfg["min_flake_rate"]))
        print()

    # Confirm flake at HEAD
    if verbose:
        print("Confirming flake at HEAD...")
    head_sample = run_n(test_id, runs, cwd=cwd)
    if verbose:
        print("  HEAD: " + str(head_sample.failures) + "/" + str(head_sample.runs)
              + " failures (rate " + str(round(head_sample.rate, 2)) + ")")

    if head_sample.rate < cfg["min_flake_rate"]:
        return Finding(
            test_id=test_id,
            status="no_flake",
            message=("test is not flaky at HEAD. Rate "
                     + str(round(head_sample.rate, 3))
                     + " < threshold " + str(cfg["min_flake_rate"])),
            after=head_sample,
        )

    # Bisect
    lo = -1   # known good
    hi = len(commits) - 1   # known flaky

    if verbose:
        print()
        print("Bisecting...")

    while hi - lo > 1:
        mid = (lo + hi) // 2
        commit = commits[mid]
        git.checkout(commit.sha, cwd=cwd)
        sample = run_n(test_id, runs, cwd=cwd)

        if verbose:
            print("  " + commit.short + "  " + str(sample.failures)
                  + "/" + str(sample.runs)
                  + "  rate=" + str(round(sample.rate, 2)))

        if sample.rate >= cfg["min_flake_rate"]:
            hi = mid
        else:
            lo = mid

    culprit = commits[hi]

    if verbose:
        print()
        print("Candidate: " + culprit.short + " - " + culprit.message)

    # Verify: run at culprit and at parent, same N, compute p-value
    git.checkout(culprit.sha, cwd=cwd)
    after = run_n(test_id, runs, cwd=cwd)

    parent_sha = git.parent_of(culprit.sha, cwd=cwd)
    git.checkout(parent_sha, cwd=cwd)
    before = run_n(test_id, runs, cwd=cwd)

    p = two_proportion_p_value(before.failures, before.runs,
                               after.failures, after.runs)

    if verbose:
        print()
        print("Verification:")
        print("  parent (" + parent_sha[:8] + "): "
              + str(before.failures) + "/" + str(before.runs)
              + " (rate " + str(round(before.rate, 2)) + ")")
        print("  culprit (" + culprit.short + "): "
              + str(after.failures) + "/" + str(after.runs)
              + " (rate " + str(round(after.rate, 2)) + ")")
        print("  p-value: " + str(round(p, 4)))

    if p > cfg["p_threshold"]:
        return Finding(
            test_id=test_id,
            status="not_found",
            culprit=culprit,
            before=before,
            after=after,
            p_value=p,
            message=("could not statistically distinguish flake rate at "
                     + culprit.short + " from its parent (p="
                     + str(round(p, 3)) + ")"),
            range_from=parent_sha[:8],
            range_to=culprit.short,
        )

    culprit.files = git.commit_files(culprit.sha, cwd=cwd)

    return Finding(
        test_id=test_id,
        status="found",
        culprit=culprit,
        before=before,
        after=after,
        p_value=p,
        message="flake rate crossed threshold at " + culprit.short,
    )
