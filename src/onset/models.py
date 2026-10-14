
"""Data model for onset."""

from dataclasses import dataclass, field, asdict


@dataclass
class Commit:
    sha: str
    short: str
    author: str
    date: str
    message: str
    files: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


@dataclass
class Sample:
    """N runs of one test at one commit."""
    commit_sha: str
    runs: int = 0
    failures: int = 0
    error_texts: list = field(default_factory=list)

    @property
    def rate(self):
        if self.runs == 0:
            return 0.0
        return self.failures / self.runs

    def to_dict(self):
        d = asdict(self)
        d["rate"] = self.rate
        return d


@dataclass
class Finding:
    test_id: str
    status: str = "unknown"      # "found" | "not_found" | "no_flake" | "error"
    culprit: Commit | None = None
    before: Sample | None = None
    after: Sample | None = None
    p_value: float = 1.0
    message: str = ""
    range_from: str = ""
    range_to: str = ""

    def to_dict(self):
        return {
            "test_id": self.test_id,
            "status": self.status,
            "culprit": self.culprit.to_dict() if self.culprit else None,
            "before": self.before.to_dict() if self.before else None,
            "after": self.after.to_dict() if self.after else None,
            "p_value": self.p_value,
            "message": self.message,
            "range_from": self.range_from,
            "range_to": self.range_to,
        }
