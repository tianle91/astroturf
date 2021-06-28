import os
import sqlite3

import pandas as pd

from astroturf.parser import parse_comment_body
from astroturf.prawtools import get_reddit


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
                done_scraping INTEGER,
                done_training INTEGER,
                done_responding INTEGER
            );
            ''')
        except Exception:
            pass


if __name__ == '__main__':

    reddit = get_reddit()
    subreddit = os.getenv('SUBREDDIT', 'AskReddit')
    db_name = 'requests.db'
    table_name = 'comments'

    initialize_table(db_name=db_name, table_name=table_name)
    stream_started = False

    for comment in reddit.subreddit(subreddit).stream.comments(skip_existing=True):
        if not stream_started:
            print('Stream started! Listening...')
            stream_started = True

        is_relevant, target_username = parse_comment_body(comment.body)
        if not is_relevant or target_username is None:
            continue
        print(
            f'comment.id:{comment.id}\n'
            f'comment.author.name:{comment.author.name}\n'
            f'comment.created_utc:{comment.created_utc}\n'
            f'comment.body:{comment.body}\n'
            f'comment.permalink:{comment.permalink}\n'
            f'target_username:{target_username}'
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
