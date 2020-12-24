import configparser

from google.cloud import storage
from praw import Reddit


def get_reddit(
    client: storage.Client,
    config_bucket: str,
    site: str = 'astroturf_bot'
) -> Reddit:
    bucket = client.bucket(config_bucket)
    praw_blob = bucket.blob('astroturf-praw.ini')
    config = configparser.ConfigParser()
    config.read_string(praw_blob.download_as_text())
    return Reddit(**config[site])
