import sqlite3


def initialize_table(db_name, table_name):
    with sqlite3.connect(db_name) as conn:
        try:
            conn.execute(f'''
            CREATE TABLE {table_name} (
                id TEXT,
                author TEXT,
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
