import sqlite3
from time import sleep

import pandas as pd

if __name__ == '__main__':
    requests_db = 'requests.db'
    table_name = 'comments'

    while True:
        with sqlite3.connect(requests_db) as conn:
            df = pd.read_sql(f'''
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
            if len(df) > 0:
                for i, row in df.iterrows():
                    print(' '.join([f'{c}: {row[c]}' for c in df.columns]))
            else:
                print('No undone')
        sleep(5)