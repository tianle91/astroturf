# https://www.digitalocean.com/community/tutorials/how-to-make-a-web-application-using-flask-in-python-3

import json
from textwrap import wrap

import requests
from flask import Flask, flash, redirect, render_template, request, url_for
from google.cloud import pubsub_v1, storage

from praw_utils import get_reddit
from status import get_trained_usernames, is_invalid

app = Flask(__name__)

# some clients and variables
client = storage.Client()
reddit = get_reddit(client, 'astroturf-dev-configs')
config_bucket = client.bucket('astroturf-dev-configs')
app.secret_key = config_bucket.blob('app_secret_key').download_as_string()
path_config = json.loads(config_bucket.blob(
    'pathConfig.json').download_as_string())
project_id = path_config['project_id']
defaulturl = path_config['defaulturl']
infer_endpoint = path_config['infer_endpoint']
update_endpoint = path_config['update_endpoint']

# publishing refresh requests
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(
    project_id, path_config['pub_refresh_request'])
status_bucket = client.bucket(path_config['status_bucket'])


def clean_string(s: str) -> str:
    return ''.join([c for c in s.lower() if c.isalnum()])


def get_wrapped(s: str) -> str:
    resl = []
    for ssub in s.split('\n'):
        resl += wrap(ssub)
    return '\n'.join(resl)


def is_invalid_url(url):
    return 'reddit.com' not in url


@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        username = request.form['requestedusername'].strip().lower()
        if is_invalid(username):
            flash('User: {} is invalid or not found!'.format(username))
            return redirect(url_for('index'))
        else:
            return redirect(url_for('infer', username=username))
    return render_template('index.html', users=get_trained_usernames())


@app.route('/infer/<username>', methods=('GET', 'POST'))
def infer(username):
    username = clean_string(username)
    updateresponse = requests.get('{update_endpoint}/status/{username}'.format(
        update_endpoint=update_endpoint,
        username=username
    )).json()
    usr_last_trained = updateresponse['model_update_dt']
    userresponse = {'username': username, 'defaulturl': defaulturl}
    if usr_last_trained is None:
        flash('No model found for User: {}. Request model training?'.format(username))
        return redirect(url_for('refresh', username=username))
    if request.method == 'POST':
        url = request.form['url']
        if is_invalid_url(url):
            if url != '':
                flash('Invalid url: {}'.format(url))
                return redirect(url_for('infer', username=username))
            url = defaulturl
        inferresponse = requests.get('{infer_endpoint}/infer/{username}?url={url}'.format(
            infer_endpoint=infer_endpoint, username=username, url=url
        )).json()
        userresponse.update({
            'url': url,
            'prompt': get_wrapped(inferresponse['prompt']),
            'response': get_wrapped(inferresponse['response']),
        })
    return render_template('infer.html', userinference=userresponse)


@app.route('/refresh/<username>', methods=('GET', 'POST'))
def refresh(username):
    username = clean_string(username)
    if is_invalid(username):
        flash('User: {} is invalid or not found!'.format(username))
        return redirect(url_for('index'))
    updateresponse = requests.get('{update_endpoint}/status/{username}'.format(
        update_endpoint=update_endpoint,
        username=username
    )).json()

    userrefresh = {
        'username': username,
        'status': str(updateresponse),
    }
    if request.method == 'POST':
        # last_update = [last_request(username), last_success(
        #     username), last_progress(username)]
        # last_update = [dt for dt in last_update if dt is not None]
        # earliest_update_possible = datetime.now(
        #     timezone.utc) - timedelta(minutes=5)
        # latest_update = max(last_update) if len(last_update) > 0 else None
        # if latest_update is not None and latest_update >= earliest_update_possible:
        #     flash('Invalid request for User: {} Try again in: {}.'.format(
        #         username, get_compact_timedelta_str_from_seconds(
        #             (latest_update - earliest_update_possible).seconds)
        #     ))
        # else:
        #     future = publisher.publish(topic_path, str.encode(username))
        #     message_id = future.result()
        #     refresh_request = status_bucket.blob(
        #         os.path.join(username, StatusFlags.refresh_request)
        #     )
        #     refresh_request.upload_from_string(message_id)
        #     flash('Submitted request to refresh User: {}. Published Message ID: {}'.format(
        #         username, message_id))
        updateresponse = requests.get('{update_endpoint}/update/{username}'.format(
            update_endpoint=update_endpoint,
            username=username
        )).json()
    return render_template('refresh.html', userrefresh=userrefresh)
