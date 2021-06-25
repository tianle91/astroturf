import os
import sqlite3
from time import sleep

import pandas as pd

from astroturf.finetune import NoInputError, dump_finetuned

if __name__ == '__main__':

    db_name = 'requests.db'
    table_name = 'comments'
    data_prefix = 'data/comment'
    model_prefix = 'model/user'

    sleep(3)

    while True:
        with sqlite3.connect(db_name) as conn:
            todo = pd.read_sql(f'''
            SELECT DISTINCT target_username 
            FROM {table_name} 
            WHERE done_scraping > 0
                AND done_training <= 0
            ''', conn)
        if len(todo) > 0:
            for user_name in todo['target_username']:
                local_data_path_user = os.path.join(data_prefix, user_name)
                local_model_path_user = os.path.join(model_prefix, user_name)
                try:
                    dump_finetuned(
                        local_data_path_user,
                        local_model_path_user,
                        block_size=16,
                        max_steps=10,
                        learning_rate=1e-4,
                    )
                except NoInputError as e:
                    print(e)
                with sqlite3.connect(db_name) as conn:
                    conn.execute(f'''
                    UPDATE {table_name}
                    SET done_training = 1
                    WHERE target_username = '{user_name}'
                    ''')
                    conn.commit()
        else:
            sleep(1)
