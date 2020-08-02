import pandas as pd
from datetime import datetime
import os
import json
import pickle
import praw

def get_context(comment, reddit):
    submission = reddit.submission(id=comment.link_id.replace('t3_', ''))
    parent_comment = None
    if not comment.parent_id == comment.link_id:
        # not a top level comment, try to retrieve parent comment
        parent_comment = reddit.comment(id=comment.parent_id.replace('t1_', ''))
    return parent_comment, submission

def get_all_context(comment, reddit):
    parent_comment, submission = get_context(comment, reddit)
    if parent_comment is None:
        # base case: is a top level comment
        parent_comments = []
        return parent_comments, submission
    else:
        parent_comments, submission = get_all_context(parent_comment, reddit)
        return (parent_comments + [parent_comment], submission)

def format_comment_as_json(comment):
    return {
        'id': comment.id, 
        'author': comment.author.name if comment.author is not None else None, 
        'body': comment.body, 
        'created_utc': comment.created_utc,
        'permalink': comment.permalink,
    }

def format_submission_as_json(submission):
    return {
        'id': submission.id,
        'subreddit': submission.subreddit.display_name,
        'title': submission.title,
        'selftext': submission.selftext,
        'permalink': submission.permalink,
    }
