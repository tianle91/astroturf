# https://www.digitalocean.com/community/tutorials/how-to-make-a-web-application-using-flask-in-python-3

import json
import os
from datetime import datetime, timedelta, timezone

import requests
from flask import Flask, flash, redirect, render_template, request, url_for
from google.cloud import pubsub_v1, storage

from praw_utils import get_reddit
from status import (get_trained_usernames, is_invalid, last_progress,
                    last_request, last_success, status)
from statusflags import StatusFlags

app = Flask(__name__)

# some clients and variables
client = storage.Client()
reddit = get_reddit(client, 'astroturf-dev-configs')
config_bucket = client.bucket('astroturf-dev-configs')
app.secret_key = config_bucket.blob('app_secret_key').download_as_string()

# publishing refresh requests
path_config = json.loads(config_bucket.blob(
    'pathConfig.json').download_as_string())
project_id = path_config['project_id']
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, path_config['pub_refresh_request'])
status_bucket = client.bucket(path_config['status_bucket'])

defaulturl = path_config['defaulturl']


def is_invalid_url(url):
    return 'reddit.com' not in url


@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        username = request.form['requestedusername']
        if is_invalid(username, reddit):
            flash('User: {} is invalid or not found!'.format(username))
            return redirect(url_for('index'))
        else:
            return redirect(url_for('infer', username=username))
    return render_template('index.html', users=sorted(get_trained_usernames()))


@app.route('/infer/<username>', methods=('GET', 'POST'))
def infer(username):
    usr_last_trained = last_success(username)
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
        inferresponse = requests.get('http://infer:8000/{username}?url={url}'.format(
            username=username, url=url
        ))
        userresponse.update({'url': url, **inferresponse.json()})
    return render_template('infer.html', userinference=userresponse)


@app.route('/refresh/<username>', methods=('GET', 'POST'))
def refresh(username):
    if is_invalid(username, reddit):
        flash('User: {} is invalid or not found!'.format(username))
        return redirect(url_for('index'))
    userrefresh = {
        'username': username,
        'status': status(username),
    }
    if request.method == 'POST':
        last_update = [last_request(username), last_success(
            username), last_progress(username)]
        last_update = [dt for dt in last_update if dt is not None]
        earliest_update_possible = datetime.now(
            timezone.utc) - timedelta(minutes=5)
        if len(last_update) > 0 and max(last_update) >= earliest_update_possible:
            flash('Invalid request for User: {} Try again in: {} seconds.'.format(
                username, (min(last_update) - earliest_update_possible).seconds
            ))
        else:
            future = publisher.publish(topic_path, str.encode(username))
            message_id = future.result()
            refresh_request = status_bucket.blob(
                os.path.join(username, StatusFlags.refresh_request)
            )
            refresh_request.upload_from_string(message_id)
            flash('Submitted request to refresh User: {}. Published Message ID: {}'.format(
                username, message_id))
    return render_template('refresh.html', userrefresh=userrefresh)
