
"""Run a test N times at a given commit and count failures."""

import os
import subprocess
import time

from dotenv import load_dotenv

from onset.models import Sample

load_dotenv()


def _timeout():
    return int(os.getenv("ONSET_TIMEOUT", "60"))


def run_n(test_id, n, cwd=".", timeout=None):
    """Run the given pytest test N times. Return a Sample."""
    timeout = timeout or _timeout()
    failures = 0
    errors = []

    for i in range(n):
        try:
            r = subprocess.run(
                ["pytest", test_id, "-q", "--no-header", "-x"],
                capture_output=True, text=True, cwd=cwd, timeout=timeout,
            )
            if r.returncode != 0:
                failures += 1
                lines = [l for l in r.stdout.splitlines() if l.strip()]
                if lines:
                    errors.append(lines[-1][:200])
        except subprocess.TimeoutExpired:
            failures += 1
            errors.append("timeout")

    return Sample(
        commit_sha="",
        runs=n,
        failures=failures,
        error_texts=errors[:5],
    )


def confirm_flake(test_id, n, min_rate, cwd="."):
    """Run the test at HEAD. If failure rate is below min_rate, return None.
    Otherwise return the Sample."""
    sample = run_n(test_id, n, cwd=cwd)
    if sample.rate < min_rate:
        return None
    return sample
