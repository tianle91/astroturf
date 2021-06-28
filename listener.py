import os
import sqlite3

import pandas as pd

from astroturf.parser import find_username
from astroturf.prawtools import get_reddit


def initialize_requests_db(db_name, table_name):
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
                done_scraping INTEGER,
                done_training INTEGER,
                done_responding INTEGER
            );
            ''')
        except Exception:
            pass


def initialize_ignore_db(db_name, table_name):
    with sqlite3.connect(db_name) as conn:
        try:
            conn.execute(f'''
            CREATE TABLE {table_name} (
                id TEXT,
                name TEXT
            );
            ''')
        except Exception:
            pass


if __name__ == '__main__':

    reddit = get_reddit()
    subreddit = os.getenv('SUBREDDIT', 'AskReddit')
    db_name = 'requests.db'
    table_name = 'comments'

    ignore_db_name = 'ignore.db'
    ignore_table_name = 'users'

    initialize_requests_db(db_name=db_name, table_name=table_name)
    initialize_ignore_db(db_name=ignore_db_name, table_name=ignore_table_name)
    stream_started = False

    for comment in reddit.subreddit(subreddit).stream.comments(skip_existing=True):
        if not stream_started:
            print('Stream started! Listening...')
            stream_started = True

        # some validation of parsed result
        target_username = find_username(comment.body)
        if target_username is not None:
            print(
                f'comment.id:{comment.id}\n'
                f'comment.author.name:{comment.author.name}\n'
                f'comment.created_utc:{comment.created_utc}\n'
                f'comment.body:{comment.body}\n'
                f'comment.permalink:{comment.permalink}\n'
                f'target_username:{target_username}'
            )
            try:
                reddit.redditor(target_username).id
            except Exception as e:
                print(e)
                print(
                    f'Will not trigger for {target_username} due to exceptions.')
                target_username = None
        if target_username is None:
            continue

        ignore = False
        with sqlite3.connect(ignore_db_name) as conn:
            in_ignore = pd.read_sql(f'''
            SELECT *
            FROM {ignore_table_name}
            WHERE name = '{comment.author.name}'
            ''', conn)
            if len(in_ignore) > 0:
                print(
                    f'Will not trigger as {comment.author.name} is in_ignore.')
                ignore = True

        if ignore:
            continue

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
