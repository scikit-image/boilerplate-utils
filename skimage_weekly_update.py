#!/usr/bin/env python

"""Print a weekly report for scikit-image repo activity in Markdown format."""

import sys
import argparse
from github import Github
from datetime import datetime, timedelta, timezone
from tqdm import tqdm


def print_list(items, *, heading=None):
    """Print number and heading from list of issues or pull requests."""
    print(f'### {heading}\n')
    if not items:
        print('none')
    else:
        state_to_emoji = {'closed': '📕', 'open': '📖'}
        for item in items:
            emoji = state_to_emoji.get(item.state, '❔')
            print(f'{emoji} [#{item.number}]({item.html_url}) {item.title}')
    print('\n')


def parse_command_line():
    """Define and parse command line options."""
    before = datetime.now().astimezone(timezone.utc)
    after = before - timedelta(days=7)

    def to_utc_datetime(s):
        return datetime.fromisoformat(s).astimezone(timezone.utc)

    parser = argparse.ArgumentParser(description=__doc__,)
    parser.add_argument('-t', '--token', help='Optional GitHub token to use.')
    parser.add_argument(
        '--before',
        help='Grab pulls or issues before this date (exclusive). '
             'Use ISO format. Defaults to now.',
        default=before,
        type=to_utc_datetime,
    )
    parser.add_argument(
        '--after',
        help='Grab pulls or issues after this date (inclusive). '
             'Use ISO format. Defaults to 7 days before now',
        default=after,
        type=to_utc_datetime,
    )
    kwargs = vars(parser.parse_args())
    return kwargs


def fetch_categorized_issues_n_prs(repo, *, start, stop):
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
        state='all',
        sort="updated",
        direction="asc",
        since=start,
    )

    new_issues = []
    updated_issues = []
    closed_issues = []

    new_prs = []
    updated_prs = []
    merged_prs = []
    closed_prs = []

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
        closed_in_range = in_report_range(item.closed_at)
        is_pr = item.pull_request is not None
        merged_in_range = is_pr and in_report_range(item.as_pull_request().merged_at)

        if is_pr:
            if merged_in_range:
                merged_prs.append(item)
            elif closed_in_range:
                closed_prs.append(item)
            if new_in_range:
                new_prs.append(item)
            if not closed_in_range and not new_in_range:
                updated_prs.append(item)

        else:
            if closed_in_range:
                closed_issues.append(item)
            if new_in_range:
                new_issues.append(item)
            if not closed_in_range and not new_in_range:
                updated_issues.append(item)

    return {
        "New pull requests": new_prs,
        "Updated pull requests (state unchanged)": updated_prs,
        "Merged pull requests": merged_prs,
        "Closed pull requests (not merged)": closed_prs,
        "New issues": new_issues,
        "Updated issues (state unchanged)": updated_issues,
        "Closed issues": closed_issues,
    }


def main(*, before, after, token=None):
    """Execute script.

    Keyword arguments are supplied by `parse_command_line()`.
    """
    g = Github(token)
    repo = g.get_repo("scikit-image/scikit-image")

    categories = fetch_categorized_issues_n_prs(repo, start=after, stop=before)

    print(f'## {after:%b %d} to {before:%b %d, %Y}\n')
    for heading, items in categories.items():
        print_list(items, heading=heading)


if __name__ == "__main__":
    kwargs = parse_command_line()
    main(**kwargs)
