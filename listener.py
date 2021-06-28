import os
import sqlite3
from typing import Optional

import pandas as pd
from praw.reddit import Comment

from astroturf.prawtools import get_context, get_reddit


def initialize_table(db_name, table_name):
    with sqlite3.connect(db_name) as conn:
        try:
            conn.execute(f'''
            CREATE TABLE {table_name} (
                id TEXT,
                author TEXT,
                created_utc REAL,
                body TEXT,
                permalink TEXT,
                target_username TEXT,
                target_permalink TEXT,
                done_scraping INTEGER,
                done_training INTEGER,
                done_responding INTEGER
            );
            ''')
        except Exception:
            pass


trigger_prefixes = ['what would',
                    'what will',
                    'what might',
                    'how would',
                    'how will',
                    'how might']
trigger_suffixes = ['say',
                    'respond',
                    'think',
                    'reply']


def is_relevant(comment: Comment) -> bool:
    """Return True iff any prefixes triggered and any suffixes triggered.
    """
    s = comment.body.lower()
    prefix_hit = any(subs in s for subs in trigger_prefixes)
    suffix_hit = any(subs in s for subs in trigger_suffixes)
    return prefix_hit and suffix_hit and 'u/' in s


def get_username_from_comment_body(s: str) -> Optional[str]:
    """Return {username} when given string of form * u/{username} *.
    """
    username = None
    if 'https://www.reddit.com/u/' in s:
        # https://www.reddit.com/u/{username}/
        prefix = 'https://www.reddit.com/u/'
        username = s[s.find(prefix) + len(prefix):].split('/')[0]
    else:
        # <whitespace> u/{username} <whitespace>
        # <whitespace> /u/{username} <whitespace>
        found_a_username = False
        for word in s.lower().split():
            if found_a_username:
                break
            for prefix in ['u/', '/u/']:
                if word.startswith(prefix):
                    username = word.replace(prefix, '')
                    found_a_username = True
                    break
    if username is not None:
        return username.lower().strip()


if __name__ == '__main__':

    reddit = get_reddit()
    subreddit = os.getenv('SUBREDDIT', 'AskReddit')
    db_name = 'requests.db'
    table_name = 'comments'

    print('Listening...')
    initialize_table(db_name=db_name, table_name=table_name)

    for comment in reddit.subreddit(subreddit).stream.comments(skip_existing=True):
        if is_relevant(comment):
            target_username = get_username_from_comment_body(comment.body)
            if target_username is not None:
                # get parent_permalink
                parent_comment, submission = get_context(comment, reddit)
                if parent_comment is not None:
                    target_permalink = parent_comment.permalink
                else:
                    target_permalink = submission.permalink
                print(
                    f'comment.id:{comment.id}\n'
                    f'comment.author.name:{comment.author.name}\n'
                    f'comment.created_utc:{comment.created_utc}\n'
                    f'comment.body:{comment.body}\n'
                    f'comment.permalink:{comment.permalink}\n'
                    f'target_username:{target_username}\n'
                    f'target_permalink:{target_permalink}'
                )
                with sqlite3.connect(db_name) as conn:
                    conn.execute(f'''
                    DELETE FROM {table_name} WHERE id = '{comment.id}'
                    ''')
                    conn.commit()
                    new_request_df = pd.DataFrame([{
                        'id': comment.id,
                        'author': comment.author.name,
                        'created_utc': comment.created_utc,
                        'body': comment.body,
                        'permalink': comment.permalink,
                        'target_username': target_username,
                        'target_permalink': target_permalink,
                        # status
                        'done_scraping': 0,
                        'done_training': 0,
                        'done_responding': 0,
                    }])
                    new_request_df.to_sql(
                        name=table_name,
                        con=conn,
                        schema=None,
                        if_exists='append',
                        index=False,
                        index_label='id',
                    )
