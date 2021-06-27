import json
import os
import sqlite3
from time import sleep

import luigi
import pandas as pd
import praw
from luigi import LocalTarget, Parameter, Task
from praw.reddit import Comment

from astroturf.prawtools import get_reddit, make_package_training


class DumpCommentContext(Task):
    comment: Comment = Parameter()
    user_name = Parameter()
    prefix = Parameter()
    reddit = Parameter()

    def output(self):
        return LocalTarget(os.path.join(
            self.prefix,
            self.user_name,
            f'{self.comment.id}.json',
        ))

    def run(self):
        f = self.output().open('w')
        f.write(json.dumps(make_package_training(self.comment, reddit)))
        f.close()


def dump_user_comments(
    user_name: str,
    prefix: str,
    reddit: praw.Reddit,
    limit: int = 100,
):
    luigi.build(
        [
            DumpCommentContext(
                comment=comment,
                user_name=user_name,
                prefix=prefix,
                reddit=reddit
            )
            for comment in reddit.redditor(user_name).comments.new(limit=limit)
        ],
        workers=1,
        local_scheduler=True
    )


if __name__ == '__main__':

    reddit = get_reddit()
    db_name = 'requests.db'
    table_name = 'comments'
    prefix = 'data/comment'

    sleep(3)  # listener initializes db

    print('Waiting to scrape...')
    os.makedirs(prefix, exist_ok=True)

    while True:
        with sqlite3.connect(db_name) as conn:
            todo = pd.read_sql(f'''
            SELECT DISTINCT target_username
            FROM {table_name}
            WHERE done_scraping <= 0
            ''', conn)
        if len(todo) > 0:
            for user_name in todo['target_username']:
                print(f'Scraping {user_name}')
                dump_user_comments(
                    user_name=user_name, prefix=prefix, reddit=reddit)
                with sqlite3.connect(db_name) as conn:
                    conn.execute(f'''
                    UPDATE {table_name}
                    SET done_scraping = 1
                    WHERE target_username = '{user_name}'
                    ''')
                    conn.commit()
        else:
            sleep(1)
