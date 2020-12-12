import configparser

import praw
from google.cloud import storage


def get_reddit(client: storage.Client, config_bucket: str, site: str = 'chennngiskhan') -> praw.Reddit:
    bucket = client.bucket(config_bucket)
    praw_blob = bucket.blob('praw.ini')
    config = configparser.ConfigParser()
    config.read_string(praw_blob.download_as_text())
    return praw.Reddit(**config[site])
