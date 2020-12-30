import json
from datetime import datetime, timezone
from typing import List, Optional

import pandas as pd
from google.cloud import storage
from google.cloud.storage import Blob
from prawcore.exceptions import NotFound

from praw_utils import get_reddit

client = storage.Client()
config_bucket = client.bucket('astroturf-dev-configs')
path_config = json.loads(config_bucket.blob(
    'pathConfig.json').download_as_string())
model_bucket = client.bucket(path_config['model_bucket'])
reddit = get_reddit(client, 'astroturf-dev-configs')

# this is the same as astroturf.finetune.model_output_fnames, don't want to load the entire module
model_output_fnames = ['pytorch_model.bin', 'config.json', 'training_args.bin']


def get_reloaded_if_exists(blob: Blob) -> Blob:
    if blob.exists():
        blob.reload()
    return blob


def get_compact_timedelta_str_from_seconds(seconds: int) -> str:
    s = seconds
    if s < 60:
        return f'{s}s'
    m = s // 60
    if m < 60:
        return f'{m}m'
    h = m // 60
    if h < 60:
        return f'{h}h'
    d = h // 24
    if d < 60:
        return f'{d}d'
    return '>60d'


def get_compact_time_since(dt: Optional[datetime]) -> str:
    utcnow = datetime.now(timezone.utc)
    s = '?'
    if dt is not None:
        s = '{} ago'.format(get_compact_timedelta_str_from_seconds(
            (utcnow - dt).seconds
        ))
    return s.rjust(len('>60d ago'))


def is_invalid(username: str) -> bool:
    if len(username) == 0:
        # not catched by NotFound (as of 2020-11-04)
        return True
    try:
        reddit.redditor(name=username).id
    except NotFound:
        return True
    return False


def has_comments(username: str) -> bool:
    for comment in reddit.redditor(username).comments.new():
        return True
    return False


def get_trained_usernames() -> List[str]:
    resl = []
    for blob in client.list_blobs(model_bucket, prefix=''):
        # {username}/model/{fname}
        blob_name_split = blob.name.split('/')
        resl.append({
            'username': blob_name_split[0],
            'fname': blob_name_split[2]
        })
    usernames = []
    for username, subdf in pd.DataFrame(resl).groupby('username'):
        subdf_fnames = subdf['fname'].unique()
        if all([s in subdf_fnames for s in model_output_fnames]):
            usernames.append(username)
    return sorted(usernames)


if __name__ == '__main__':
    print(get_trained_usernames())
