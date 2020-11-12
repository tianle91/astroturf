# https://www.digitalocean.com/community/tutorials/how-to-make-a-web-application-using-flask-in-python-3

import json

from flask import Flask, render_template, request, flash, redirect, url_for
from google.cloud import pubsub_v1
from google.cloud import storage

from main import refresh_local_models, simulate_redditor_response, is_invalid, last_trained, last_refreshed, status, get_trained_usernames
from praw_utils import get_reddit

app = Flask(__name__)

# some clients and variables
client = storage.Client()
reddit = get_reddit(client, 'astroturf-dev-configs')
config_bucket = client.bucket('astroturf-dev-configs')
app.secret_key = config_bucket.blob('app_secret_key').download_as_string()

# publishing refresh requests
path_config = json.loads(config_bucket.blob('pathConfig.json').download_as_string())
project_id = path_config['project_id']
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, 'model_refresh_requests')

defaulturl = 'https://www.reddit.com/r/toronto/comments/hkjyjn/city_issues_trespassing_orders_to_demonstrators/fwt4ifw'


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
    return render_template('index.html', users=get_trained_usernames())


@app.route('/infer/<username>', methods=('GET', 'POST'))
def infer(username):
    usr_last_trained = last_trained(username)
    usr_last_refreshed = last_refreshed(username)
    userresponse = {
        'username': username,
        'defaulturl': defaulturl,
        'usrlasttrained': usr_last_trained,
        'usrlastrefreshed': usr_last_refreshed
    }
    if usr_last_trained is None:
        flash('No model found for User: {}. Request model training?'.format(username))
        return redirect(url_for('refresh', username=username))
    refresh_local_models(username)
    if request.method == 'POST':
        url = request.form['url']
        if is_invalid_url(url):
            if url != '':
                flash('Invalid url: {}'.format(url))
                return redirect(url_for('infer', username=username))
            url = defaulturl
        userresponse.update({'url': url, **simulate_redditor_response(username, url)})
    return render_template('infer.html', userinference=userresponse)


@app.route('/refresh/<username>', methods=('GET', 'POST'))
def refresh(username):
    usr_last_trained = last_trained(username)
    usr_last_refreshed = last_refreshed(username)
    if is_invalid(username, reddit):
        flash('User: {} is invalid or not found!'.format(username))
        return redirect(url_for('index'))
    userrefresh = {
        'username': username,
        'status': status(username),
    }
    if request.method == 'POST':
        future = publisher.publish(topic_path, str.encode(username))
        message_id = future.result()
        flash('Submitted request to refresh User: {}. Published Message ID: {}'.format(username, message_id))
        return redirect(url_for('index'))
    return render_template('refresh.html', userrefresh=userrefresh)
