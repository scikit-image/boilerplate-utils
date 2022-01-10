#!/usr/bin/env python
import argparse
from github import Github
from datetime import datetime, timedelta


def print_list(l, title=None):
    """Print number and title from list of PullRequest of Issue objects."""
    print(f'## {title}\n')
    if not l:
        print('none')
    else:
        for el in l:
            print(f'#{el.number} {el.title}')
    print('\n')


def create_argument_parser():
    today = datetime.fromisoformat(datetime.today().isoformat().split('T')[0])
    parser = argparse.ArgumentParser(
        description='Generate a weekly report for scikit-image repo activity',
    )
    parser.add_argument('-t', '--token', help='The GitHub token to use.')
    parser.add_argument(
        '--before',
        help='Grab pulls or issues before this date (exclusive). '
             'Use YYYY-MM-DD format.',
        default=today,
        type=datetime.fromisoformat,
    )
    parser.add_argument(
        '--after',
        help='Grab pulls or issues after this date (inclusive). '
             'Use YYYY-MM-DD format.',
        default=today - timedelta(days=7),
        type=datetime.fromisoformat,
    )
    return parser


def main():
    """
    token : str
        Github token.
    number_covered_days : int
        Number of days to cover in the report.
    """

    parser = create_argument_parser()
    args = parser.parse_args()
    # Compute the starting time
    now = args.before
    start = args.after

    print(
        f'# {start.year}/{start.month}/{start.day} - '
        f'{now.year}/{now.month}/{now.day}'
    )

    g = Github(args.token)
    repo = g.get_repo("scikit-image/scikit-image")


    # --------------------- Pull requests ------------------------------
    pulls = repo.get_pulls(state='all')
    # We need these numbers to distinguish prs from issues
    pr_numbers = [p.number for p in pulls[:400]]

    def in_date_range(date):
        return date >= start and date < now

    new_pulls = [pull for pull in pulls[:100] if in_date_range(pull.created_at)]
    print_list(new_pulls, 'New pull requests open last week')

    closed_prs = repo.get_pulls(state='closed')

    closed_and_not_merged_prs = [p for p in closed_prs[:200]
            if p.merged_at is None and in_date_range(p.closed_at)]
    print_list(closed_and_not_merged_prs, 'Closed pull requests (not merged)')

    merged_prs = [p for p in closed_prs[:200]
            if p.merged_at and in_date_range(p.merged_at)]
    print_list(merged_prs, 'Merged pull requests')

    open_prs = repo.get_pulls(state='open')
    updated_prs = [p for p in open_prs[:100]
            if p.created_at <= start and p.updated_at and in_date_range(p.updated_at)]
    print_list(updated_prs, 'Older pull requests with new comments or commits')

    # ------------------ Issues -------------------------------------------
    issues = repo.get_issues(since=start, state='all')

    new_issues = [issue for issue in issues if in_date_range(issue.created_at)]
    new_issues = [issue for issue in new_issues
            if issue.number not in pr_numbers]
    print_list(new_issues, 'New issues')

    new_comments = [issue for issue in issues
            if issue.created_at < start and in_date_range(issue.updated_at)
            and issue.state == 'open']
    existing_issues_with_new_comments = [el for el in new_comments
            if el.number not in pr_numbers]
    print_list(existing_issues_with_new_comments, 'Older issues updated last week')

    closed_issues = [issue for issue in issues if issue.closed_at
            and in_date_range(issue.closed_at)]
    closed_issues = [issue for issue in closed_issues
            if issue.number not in pr_numbers]
    print_list(closed_issues, 'Closed issues')


if __name__ == "__main__":
    # Call with `-t GITHUBTOKEN`
    # Generate it on github website,
    # in the scope, select "Repo".
    main()
