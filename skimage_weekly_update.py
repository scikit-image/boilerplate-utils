#!/usr/bin/env python

"""Print a weekly report for scikit-image repo activity in Markdown format."""

# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "pygithub>=2.3",
#   "tqdm",
# ]
# ///

import sys
import argparse
import dataclasses
from github import Github
from datetime import datetime, timedelta, timezone
from tqdm import tqdm


def print_list(items, *, heading=None):
    """Print number and heading from list of issues or pull requests."""
    print(f"### {heading} ({len(items)})\n")
    if not items:
        print("none")
    else:
        sorted_items = sorted(items, key=lambda x: x.number)
        sorted_items = sorted(sorted_items, key=lambda x: x.state, reverse=True)
        for item in sorted_items:
            print(f"- [#{item.number}]({item.html_url}) {item.title}")
    print("\n")


def parse_command_line():
    """Define and parse command line options."""
    before = datetime.now().astimezone(timezone.utc)
    after = before - timedelta(days=7)

    def to_utc_datetime(s):
        return datetime.fromisoformat(s).astimezone(timezone.utc)

    parser = argparse.ArgumentParser(
        description=__doc__,
    )
    parser.add_argument("-t", "--token", help="Optional GitHub token to use.")
    parser.add_argument(
        "--before",
        help="Grab pulls or issues before this date (exclusive). "
        "Use ISO format. Defaults to now.",
        default=before,
        type=to_utc_datetime,
    )
    parser.add_argument(
        "--after",
        help="Grab pulls or issues after this date (inclusive). "
        "Use ISO format. Defaults to 7 days before now",
        default=after,
        type=to_utc_datetime,
    )
    kwargs = vars(parser.parse_args())
    return kwargs


@dataclasses.dataclass(slots=True)
class Categories:
    """Collect categorized issues and pull requests."""

    new_issues: list = dataclasses.field(default_factory=list)
    closed_issues: list = dataclasses.field(default_factory=list)
    other_active_issues: list = dataclasses.field(default_factory=list)
    new_prs: list = dataclasses.field(default_factory=list)
    closed_prs: list = dataclasses.field(default_factory=list)
    other_active_prs: list = dataclasses.field(default_factory=list)

    @property
    def new_open_issues(self):
        open_issues = [i for i in self.new_issues if i.state == "open"]
        return open_issues

    @property
    def new_open_prs(self):
        open_prs = [p for p in self.new_prs if p.state == "open"]
        return open_prs

    @classmethod
    def from_report_range(cls, repo, *, start, stop) -> "Categories":
        """Fetch issues and PRs in the given time frame and sort into categories.

        Parameters
        ----------
        repo : github.Repository
        start, stop : datetime
            Two datetimes defining the report window from  `start` (included) to `stop`
            (excluded). Datetimes must be timezone aware.

        Returns
        -------
        items : dict[str, list[github.Issue]]
            GitHub issues (including PRs) in the report window, sorted into
            categories.
        """
        issues_n_prs = repo.get_issues(
            state="all",
            sort="updated",
            direction="asc",
            since=start,
        )
        categories = cls()

        def in_report_range(date):
            if date is None:
                return False
            else:
                return start <= date < stop

        for item in tqdm(
            issues_n_prs,
            desc="Fetching and sorting into categories (may break early)",
            total=issues_n_prs.totalCount,
            file=sys.stderr,
        ):
            if not in_report_range(item.updated_at):
                # Assumes that items are sorted, and the first items starts within
                # the valid range (see `since=start` above)
                break

            new_in_range = in_report_range(item.created_at)
            closed_in_range = in_report_range(item.closed_at) and item.state == "closed"
            is_pr = item.pull_request is not None

            if is_pr:
                if new_in_range:
                    categories.new_prs.append(item)
                if closed_in_range:
                    categories.closed_prs.append(item)
                if not new_in_range and not closed_in_range:
                    categories.other_active_prs.append(item)
            else:
                if new_in_range:
                    categories.new_issues.append(item)
                if closed_in_range:
                    categories.closed_issues.append(item)
                if not new_in_range and not closed_in_range:
                    categories.other_active_issues.append(item)

        return categories


def main(*, before, after, token=None):
    """Execute script.

    Keyword arguments are supplied by `parse_command_line()`.
    """
    g = Github(token)
    repo = g.get_repo("scikit-image/scikit-image")

    categories = Categories.from_report_range(repo, start=after, stop=before)

    print(f"## {after:%b %d} to {before:%b %d, %Y}\n")

    for heading, items in {
        "New open pull requests": categories.new_open_prs,
        "Closed pull requests": categories.closed_prs,
        "Other active pull requests": categories.other_active_prs,
        "New open issues": categories.new_open_issues,
        "Closed issues": categories.closed_issues,
        "Other active issues": categories.other_active_issues,
    }.items():
        print_list(items, heading=heading)

    total_issue_diff = len(categories.new_issues) - len(categories.closed_issues)
    total_pr_diff = len(categories.new_prs) - len(categories.closed_prs)
    print(f"Open pull requests: {total_pr_diff:+}")
    print(f"Open issues: {total_issue_diff:+}")


if __name__ == "__main__":
    kwargs = parse_command_line()
    main(**kwargs)
