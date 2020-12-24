import json
from time import sleep, time

import requests
from google.cloud import storage
from praw.reddit import Comment, Reddit
from praw.objector import RedditAPIException

from astroturf.prawtools import get_context
from status import get_trained_usernames, is_invalid

# some clients and variables
client = storage.Client()
config_bucket = client.bucket('astroturf-dev-configs')
path_config = json.loads(config_bucket.blob(
    'pathConfig.json').download_as_string())
infer_endpoint = path_config['infer_endpoint']
update_endpoint = path_config['update_endpoint']


reply_template = """
u/{username} might reply:

{response}

---
I'm a DistilGPT2 bot finetuned using user comments with 
[Huggingface's Transformers](https://github.com/huggingface/transformers).
Play around with the UI at [64.137.143.175](http://64.137.143.175).
Source code at [tianle91/astroturf](https://github.com/tianle91/astroturf) (currently private).
"""

trigger_prefixes = ['what would',
                    'what will',
                    'what might',
                    'how may']
trigger_suffixes = ['say',
                    'respond',
                    'think']


def get_username_from_comment_body(s: str):
    """Return {username} when given string of form * u/{username} *.
    """
    if 'https://www.reddit.com/u/' in s:
        # https://www.reddit.com/u/{username}/
        prefix = 'https://www.reddit.com/u/'
        username = s[s.find(prefix)+len(prefix):].split('/')[0]
    else:
        # <whitespace> u/{username} <whitespace>
        username = [
            subs.replace('u/', '')
            for subs in s.lower().split() if subs.startswith('u/')
        ][0]
    return username.lower().strip()


def is_relevant(comment: Comment) -> bool:
    """Return True iff any prefixes triggered and any suffixes triggered.
    """
    s = comment.body.lower()
    prefix_hit = any(subs in s for subs in trigger_prefixes)
    suffix_hit = any(subs in s for subs in trigger_suffixes)
    return prefix_hit and suffix_hit and 'u/' in s


def format_reply(username: str, response: str) -> str:
    quoted_response = '\n'.join(['> ' + s for s in response.split('\n')])
    return reply_template.format(username=username, response=quoted_response)


def respond_to_trigger_comment(
    comment: Comment,
    reddit: Reddit,
    submit_reply=True,
    sleep_wait=60,
    max_wait=600,
    verbose=1
) -> None:
    """Given a trigger comment, reply to the comment with a prediction.
    """
    if verbose > 0:
        print(f'comment.body: {comment.body}')
    username = get_username_from_comment_body(comment.body)
    if is_invalid(username):
        print(f'Did not find valid username: {username}')
        return None

    # check that user has a model
    training_requested = False
    wait = 0
    while username not in get_trained_usernames() and wait < max_wait:
        if verbose > 0:
            print(f'username:{username} not trained')
        if not training_requested:
            updateresponse = requests.get('{update_endpoint}/update/{username}'.format(
                update_endpoint=update_endpoint,
                username=username
            )).json()
            training_requested = True
            if verbose > 0:
                print(f'training requested!\n{updateresponse}')
        print(f'waiting for training to complete.')
        wait += sleep_wait
        if wait >= max_wait:
            print(f'timeout. {wait} >= {max_wait}')
        else:
            sleep(f'sleep for {sleep_wait}')

    # get parent of comment, because that's the prompt
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
        print(f'reply_text:\n{reply_text}')

    # wait to reply
    while submit_reply:
        submitted_reply = False
        try:
            comment.reply(reply_text)
            submitted_reply = True
        except RedditAPIException as e:
            print(f'{e.message} Waiting for {sleep_wait}')
            sleep(sleep_wait)
        if submitted_reply:
            break
    return reply_text


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='bot for astroturf.')
    parser.add_argument('--subreddit', type=str, default='AskReddit')
    parser.add_argument('--site', type=str, default='astroturf_bot')
    args = parser.parse_args()

    sleep(30)  # infer service takes some time to spin up
    print('Ready')

    from praw_utils import get_reddit
    reddit = get_reddit(
        client, config_bucket='astroturf-dev-configs', site=args.site)

    # # testing on a triggering comment
    # trigger_comment = reddit.comment(
    #     url='https://www.reddit.com/r/AskReddit/comments/kjbam6/youre_78_years_old_youve_reached_the_end_of_your/ggx2nmb')
    # respond_to_trigger_comment(trigger_comment, reddit, submit_reply=False)

    for comment in reddit.subreddit(args.subreddit).stream.comments(skip_existing=True):
        api_remaining = reddit.auth.limits['remaining']
        print(
            f'Steaming comments from {args.subreddit}. Remaining: {api_remaining}')
        if is_relevant(comment):
            respond_to_trigger_comment(comment, reddit, submit_reply=True)
        if api_remaining < 100:
            while time() <= reddit.auth.limits['reset_timestamp']:
                print(
                    f"Waiting for reset. {time()} <= {reddit.auth.limits['reset_timestamp']}")
                sleep(10)
