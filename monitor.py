import sqlite3
from time import sleep

import pandas as pd

if __name__ == '__main__':
    requests_db = 'requests.db'
    table_name = 'comments'

    ignore_db_name = 'ignore.db'
    ignore_table_name = 'users'

    sleep(3)  # listener initializes db

    while True:
        with sqlite3.connect(requests_db) as conn:
            undone_df = pd.read_sql(f'''
            SELECT
                id,
                author,
                created_utc,
                target_username,
                done_scraping,
                done_training,
                done_responding
            FROM {table_name}
            WHERE done_scraping <= 0
                OR done_training <= 0
                OR done_responding <= 0
            ORDER BY created_utc DESC
            LIMIT 10
            ''', conn)
        with sqlite3.connect(ignore_db_name) as conn:
            ignore_count_df = pd.read_sql(f'''
            SELECT COUNT(*) AS count
            FROM {ignore_table_name}
            ''', conn)
            ignore_count = ignore_count_df['count'].iloc[0]

        if len(undone_df) > 0:
            for i, row in undone_df.iterrows():
                print(' '.join([f'{c}: {row[c]}' for c in undone_df.columns]))
        print(
            f'Pending requests: {len(undone_df)}, '
            f'ignore_count: {ignore_count}\n'
        )
        sleep(5)
