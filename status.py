import json
from datetime import datetime, timezone
from typing import List, Optional

from google.cloud import storage
from google.cloud.storage import Blob
from praw import Reddit
from prawcore.exceptions import NotFound

from praw_utils import get_reddit

client = storage.Client()
config_bucket = client.bucket('astroturf-dev-configs')
path_config = json.loads(config_bucket.blob(
    'pathConfig.json').download_as_string())
model_bucket = client.bucket(path_config['model_bucket'])
status_bucket = client.bucket(path_config['status_bucket'])
reddit = get_reddit(client, 'astroturf-dev-configs')


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


def is_invalid(username: str, r: Reddit) -> bool:
    if len(username) == 0:
        # not catched by NotFound (as of 2020-11-04)
        return True
    try:
        r.redditor(name=username).id
    except NotFound:
        return True
    return False
