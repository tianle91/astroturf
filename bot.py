import json
from time import sleep

import requests
from google.cloud import storage
from praw.reddit import Comment, Reddit

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

---
{response}

---
About:
- I'm a DistilGPT2 bot finetuned using user comments with [Huggingface's Transformers](https://github.com/huggingface/transformers).
- Play around with the UI at [64.137.143.175](http://64.137.143.175).
- Source code at [tianle91/astroturf](https://github.com/tianle91/astroturf) (currently private).
"""

trigger_prefixes = ['what would u/',
                    'what will u/',
                    'what might u/',
                    'how may u/']
trigger_suffixes = ['say',
                    'respond',
                    'think']


def get_username_from_comment_body(s: str):
    """Return {username} when given string of form * u/{username} *.
    """
    username_candidates = [
        subs for subs in s.lower().split() if subs.startswith('u/')]
    if len(username_candidates) > 0:
        return username_candidates[0].replace('u/', '')


def is_relevant(comment: Comment) -> bool:
    """Return True iff any prefixes triggered and any suffixes triggered.
    """
    s = comment.body.lower()
    prefix_hit = any(subs in s for subs in trigger_prefixes)
    suffix_hit = any(subs in s for subs in trigger_suffixes)
    return prefix_hit and suffix_hit


def format_reply(username: str, response: str) -> str:
    quoted_response = '\n'.join(['> ' + s for s in response.split('\n')])
    return reply_template.format(username=username, response=quoted_response)


def respond_to_trigger_comment(
    comment: Comment,
    reddit: Reddit,
    submit_reply=True,
    sleep_wait=30,
    max_wait=300,
    verbose=1
) -> None:
    """Given a trigger comment, reply to the comment with a prediction.
    """
    if verbose > 0:
        print(f'comment.body: {comment.body}')
    username = get_username_from_comment_body(comment.body)
    if is_invalid(username):
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
        sleep(sleep_wait)
        wait += sleep_wait
        if wait >= max_wait:
            print(f'Timeout!\ncomment.id:{comment.id}, username:{username}')
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
    if submit_reply:
        comment.reply(reply_text)
    return reply_text


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='bot for astroturf.')
    parser.add_argument('--subreddit', type=str, default='AskReddit')
    args = parser.parse_args()

    sleep(30)  # infer service takes some time to spin up
    print('Ready')

    from praw_utils import get_reddit
    reddit = get_reddit(client, config_bucket='astroturf-dev-configs')

    # # testing on a triggering comment
    # trigger_comment = reddit.comment(
    #     url='https://www.reddit.com/r/AskReddit/comments/kjbam6/youre_78_years_old_youve_reached_the_end_of_your/ggx2nmb')
    # respond_to_trigger_comment(trigger_comment, reddit, submit_reply=False)

    for comment in reddit.subreddit(args.subreddit).stream.comments(skip_existing=True):
        print(f'Steaming comments from {args.subreddit}')
        print(
            f'''reddit.auth.limits['remaining']: {reddit.auth.limits['remaining']}''')
        if is_relevant(comment):
            respond_to_trigger_comment(comment, reddit, submit_reply=True)
