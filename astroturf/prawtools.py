import configparser

from praw import Reddit
from praw.models import Comment, Submission


def get_reddit(path: str = 'praw.ini', site: str = 'astroturf_bot') -> Reddit:
    with open(path) as f:
        config = configparser.ConfigParser()
        config.read_string(f.read())
        return Reddit(**config[site])


def get_context(comment: Comment, reddit: Reddit):
    submission = reddit.submission(id=comment.link_id.replace('t3_', ''))
    parent_comment = None
    if not comment.parent_id == comment.link_id:
        # not a top level comment, try to retrieve parent comment
        parent_comment = reddit.comment(
            id=comment.parent_id.replace('t1_', ''))
    return parent_comment, submission


def get_all_context(comment: Comment, reddit: Reddit):
    parent_comment, submission = get_context(comment, reddit)
    if parent_comment is None:
        # base case: is a top level comment
        parent_comments = []
        return parent_comments, submission
    else:
        parent_comments, submission = get_all_context(parent_comment, reddit)
        return (parent_comments + [parent_comment], submission)


def format_comment_as_json(comment: Comment):
    return {
        'id': comment.id,
        'author': comment.author.name if comment.author is not None else None,
        'body': comment.body,
        'created_utc': comment.created_utc,
        'permalink': comment.permalink,
    }


def format_submission_as_json(submission: Submission):
    return {
        'id': submission.id,
        'subreddit': submission.subreddit.display_name,
        'title': submission.title,
        'selftext': submission.selftext,
        'permalink': submission.permalink,
    }


def make_package_training(comment: Comment, reddit: Reddit):
    parent_comment, submission = get_context(comment, reddit)
    return {
        'comment': format_comment_as_json(comment),
        'parent_comment': None if parent_comment is None else format_comment_as_json(parent_comment),
        'submission': format_submission_as_json(submission)
    }


def make_package_infer_comment(comment: Comment, reddit: Reddit):
    _, submission = get_context(comment, reddit)
    return {
        'comment': None,
        'parent_comment': format_comment_as_json(comment),
        'submission': format_submission_as_json(submission)
    }


def make_package_infer_submission(submission: Submission):
    return {
        'comment': None,
        'parent_comment': None,
        'submission': format_submission_as_json(submission)
    }
