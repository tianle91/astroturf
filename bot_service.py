import json
from time import sleep

from google.cloud import pubsub_v1, storage
from praw.reddit import Comment

# some clients and variables
client = storage.Client()
config_bucket = client.bucket('astroturf-dev-configs')
path_config = json.loads(config_bucket.blob(
    'pathConfig.json').download_as_string())
project_id = path_config['project_id']
infer_endpoint = path_config['infer_endpoint']
update_endpoint = path_config['update_endpoint']


# publishing to pub_bot_response_request
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(
    project_id, path_config['pub_bot_response_request'])

trigger_prefixes = ['what would',
                    'what will',
                    'what might',
                    'how may']
trigger_suffixes = ['say',
                    'respond',
                    'think']


def is_relevant(comment: Comment) -> bool:
    """Return True iff any prefixes triggered and any suffixes triggered.
    """
    s = comment.body.lower()
    prefix_hit = any(subs in s for subs in trigger_prefixes)
    suffix_hit = any(subs in s for subs in trigger_suffixes)
    return prefix_hit and suffix_hit and 'u/' in s


if __name__ == '__main__':
    import argparse

    from praw_utils import get_reddit

    parser = argparse.ArgumentParser(
        description='bot service for astroturf.')
    parser.add_argument('--subreddit', type=str, default='AskReddit')
    parser.add_argument('--site', type=str, default='astroturf_bot')
    args = parser.parse_args()

    sleep(30)  # infer service takes some time to spin up
    print('Ready')

    reddit = get_reddit(
        client, config_bucket='astroturf-dev-configs', site=args.site)

    pub_futures = []
    for comment in reddit.subreddit(args.subreddit).stream.comments(skip_existing=True):
        if is_relevant(comment):
            future = publisher.publish(
                topic_path,
                data=str.encode('https://www.reddit.com/'+comment.permalink)
            )
            pub_futures.append(future)
        if len(pub_futures) > 10:
            message_ids = [f.result() for f in pub_futures]
            print(message_ids)
            pub_futures = []
