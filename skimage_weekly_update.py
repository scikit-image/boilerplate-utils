from github import Github
from datetime import datetime

# Change start date here
start = datetime(2020, 4, 6)


def print_list(l, title=None):
    """From list of PullRequest of Issue objects,
    print their number and title.
    """
    print('## ' + title)
    if not l:
        print('none')
    else:
        for el in l:
            print('#%d' %el.number, el.title)
    print('\n')

g = Github("your own token here")
repo = g.get_repo("scikit-image/scikit-image")


# --------------------- Pull requests ------------------------------
pulls = repo.get_pulls(state='all')
# We need these numbers to distinguish prs from issues
pr_numbers = [p.number for p in pulls[:400]]

new_pulls = [pull for pull in pulls[:100] if pull.created_at >= start]
print_list(new_pulls, 'new pull requests open last week')

closed_prs = repo.get_pulls(state='closed')

closed_and_not_merged_prs = [p for p in closed_prs[:200]
        if p.merged_at is None and p.closed_at >= start ]
print_list(closed_and_not_merged_prs, 'closed pull requests (not merged)')

merged_prs = [p for p in closed_prs[:200]
        if p.merged_at and p.merged_at >= start]
print_list(merged_prs, 'merged pull requests')

open_prs = repo.get_pulls(state='open')
updated_prs = [p for p in open_prs[:100]
        if p.created_at <= start and p.updated_at and p.updated_at >= start]
print_list(updated_prs, 'Older pull requests with new comments or commits')

# ------------------ Issues -------------------------------------------
issues = repo.get_issues(since=start, state='all')

new_issues = [issue for issue in issues if issue.created_at >= start]
print_list(new_issues, 'new issues')

new_comments = [issue for issue in issues
        if issue.created_at < start and issue.updated_at >= start
        and issue.state == 'open']
existing_issues_with_new_comments = [el for el in new_comments
        if el.number not in pr_numbers]
print_list(existing_issues_with_new_comments, 'older issues updated last week')

closed_issues = [issue for issue in issues if issue.closed_at
        and issue.closed_at >= start]
closed_issues = [issue for issue in closed_issues
        if issue.number not in pr_numbers]
print_list(closed_issues, 'closed issues')
