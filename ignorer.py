import sqlite3
from time import sleep

import pandas as pd
from praw.models import Message

from astroturf.prawtools import get_reddit

if __name__ == '__main__':

    reddit = get_reddit()
    db_name = 'requests.db'

    ignore_db_name = 'ignore.db'
    ignore_table_name = 'users'

    sleep(3)  # listener initializes db

    print('Monitoring inbox...')

    while True:
        for item in reddit.inbox.stream():
            if not isinstance(item, Message):
                continue
            item: Message = item
            if 'ignore' not in item.body.lower():
                continue
            print(f'Recevied ignore request from {item.author.name}')
            with sqlite3.connect(ignore_db_name) as conn:
                in_ignore = pd.read_sql(f'''
                SELECT *
                FROM {ignore_table_name}
                WHERE name = '{item.author.name}'
                ''', conn)

            if len(in_ignore) > 0:
                item.author.message(
                    subject=item.subject,
                    message='Already in ignored list.'
                )
                print(
                    f'Replied to {item.author.name}: Already in ignored list.')
            else:
                with sqlite3.connect(ignore_db_name) as conn:
                    new_ignore_df = pd.DataFrame([{
                        'id': item.author.id,
                        'name': item.author.name,
                    }])
                    new_ignore_df.to_sql(
                        name=ignore_table_name,
                        con=conn,
                        schema=None,
                        if_exists='append',
                        index=False,
                        index_label='id',
                    )
                item.author.message(
                    subject=item.subject,
                    message='Added to ignored list.'
                )
                print(f'Replied to {item.author.name}: Added to ignored list.')
            item.mark_read()
