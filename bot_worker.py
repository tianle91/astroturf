import json
from datetime import datetime, timedelta, timezone
from time import sleep
from typing import Optional

import requests
from google.cloud import pubsub_v1, storage
from praw.objector import RedditAPIException
from praw.reddit import Comment, Reddit

from astroturf.prawtools import get_context
from status import get_trained_usernames, is_invalid

# some clients and variables
client = storage.Client()
config_bucket = client.bucket('astroturf-dev-configs')
path_config = json.loads(config_bucket.blob(
    'pathConfig.json').download_as_string())
project_id = path_config['project_id']
infer_endpoint = path_config['infer_endpoint']
update_endpoint = path_config['update_endpoint']


# subscribing to sub_bot_response_request
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(
    project_id, path_config['sub_bot_response_request'])


reply_template = """
[u/{username}](https://reddit-user-analyser.netlify.app/#{username}) might reply:

{response}

---
I'm a DistilGPT2 model finetuned with user comments using [Huggingface's Transformers](https://github.com/huggingface/transformers).
Play around with the UI at [64.137.143.175](http://64.137.143.175).
Source code at [tianle91/astroturf](https://github.com/tianle91/astroturf) (currently private).
"""


def get_username_from_comment_body(s: str) -> Optional[str]:
    """Return {username} when given string of form * u/{username} *.
    """
    # TODO: unit test
    username = None
    if 'https://www.reddit.com/u/' in s:
        # https://www.reddit.com/u/{username}/
        prefix = 'https://www.reddit.com/u/'
        username = s[s.find(prefix)+len(prefix):].split('/')[0]
    else:
        # <whitespace> u/{username} <whitespace>
        # <whitespace> /u/{username} <whitespace>
        found_a_username = False
        for word in s.lower().split():
        	if found_a_username:
        		break
        	for prefix in ['u/', '/u/']:
        		if word.startswith(prefix):
        			username = word.replace(prefix, '')
        			found_a_username = True
        			break
    if username is not None:
        return username.lower().strip()


def format_reply(username: str, response: str) -> str:
    quoted_response = '\n'.join(['> ' + s for s in response.split('\n')])
    return reply_template.format(username=username, response=quoted_response)


def respond_to_trigger_comment(
    comment: Comment,
    reddit: Reddit,
    submit_reply=True,
    sleep_wait=30,
    max_wait=3600,  # 1h
    verbose=1
) -> None:
    """Given a trigger comment, reply to the comment with a prediction.
    """
    # TODO: refactor
    if verbose > 0:
        print(
            f'Triggered comment body: {comment.body} url: {comment.permalink}')
    username = get_username_from_comment_body(comment.body)
    if is_invalid(username) or username is None:
        print(f'Invalid username parsed: {username}')
        return None

    # status on the user
    updateresponse = requests.get('{update_endpoint}/status/{username}'.format(
        update_endpoint=update_endpoint,
        username=username
    )).json()
    model_update_dt = updateresponse['model_update_dt']
    now_dt = datetime.now(tz=timezone.utc)
    last_update_is_too_old = False
    if model_update_dt is not None:
        last_update_is_too_old = datetime.fromisoformat(
            model_update_dt) + timedelta(days=1) <= now_dt
    to_update = model_update_dt is None or last_update_is_too_old

    if to_update:
        updateresponse = requests.get('{update_endpoint}/update/{username}'.format(
            update_endpoint=update_endpoint,
            username=username
        )).json()
        if verbose > 0:
            print(f'Training requested: {updateresponse}')

    # wait for user to have model available, note that no wait if last_update_is_too_old
    wait = 0
    while username not in get_trained_usernames():
        if verbose > 0:
            print(f'Valid username has no trained model: {username}')
        wait += sleep_wait
        if wait >= max_wait:
            print(f'Waiting for trained model timed out: {wait} >= {max_wait}')
            return None
        else:
            print(
                f'Waiting for trained model: {wait} < {max_wait}. Sleep for {sleep_wait}')
            sleep(sleep_wait)

    # get url of parent, because that's the prompt
    parent_comment, submission = get_context(comment, reddit)
    url = parent_comment.permalink if parent_comment is not None else submission.permalink
    url = 'https://www.reddit.com' + url
    if verbose > 0:
        print(f'username: {username}, url:{url}')

    # get response from infer_endpoint
    inferresponse = requests.get('{infer_endpoint}/infer/{username}?url={url}'.format(
        infer_endpoint=infer_endpoint, username=username, url=url
    )).json()
    # format and reply
    reply_text = format_reply(username, inferresponse['response'])
    if verbose > 0:
        print(f'Reply text:\n{reply_text}')

    # wait to reply
    submitted_reply = False
    while submit_reply and not submitted_reply:
        if wait >= max_wait:
            print(f'Waiting to submit reply timed out: {wait} >= {max_wait}')
            break
        try:
            comment.reply(reply_text)
            submitted_reply = True
        except RedditAPIException as e:
            for sube in e.items:
                print(f'{sube.error_type}: {sube.message}')
                if 'has been deleted' in sube.message:
                    print('Triggering comment has been deleted')
                    submit_reply = False
                    return reply_text
            print(f'Waiting to submit reply: {wait} >= {max_wait} sleep(60)')
            sleep(60)
            wait += sleep_wait
    return reply_text


if __name__ == '__main__':
    import argparse

    from praw_utils import get_reddit

    parser = argparse.ArgumentParser(
        description='bot worker for astroturf.')
    parser.add_argument('--site', type=str, default='astroturf_bot')
    args = parser.parse_args()

    reddit = get_reddit(
        client, config_bucket='astroturf-dev-configs', site=args.site)

    sleep(30)  # infer service takes some time to spin up
    
    print('Ready')
    while True:
        response = subscriber.pull(
            request={"subscription": subscription_path, "max_messages": 1})

        ack_ids = []
        url = None
        for msg in response.received_messages:
            url = msg.message.data.decode('utf-8')
            print(f"Received message: {url}")
            ack_ids.append(msg.ack_id)

        if len(ack_ids) > 0 and url is not None:
            subscriber.acknowledge(
                request={"subscription": subscription_path, "ack_ids": ack_ids})
            comment = reddit.comment(url=url)
            respond_to_trigger_comment(comment, reddit, submit_reply=True)
