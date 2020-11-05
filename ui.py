# https://www.digitalocean.com/community/tutorials/how-to-make-a-web-application-using-flask-in-python-3

import json
import os
from typing import Optional

from flask import Flask, render_template, request, flash, redirect, url_for
from google.cloud import pubsub_v1
from google.cloud import storage
from praw import Reddit
from prawcore.exceptions import NotFound

from main import refresh_local_models, simulate_redditor_response
from praw_utils import get_reddit

app = Flask(__name__)
client = storage.Client()

# some clients and variables
reddit = get_reddit(client, 'astroturf-dev-configs')
config_bucket = client.bucket('astroturf-dev-configs')
app.secret_key = config_bucket.blob('app_secret_key').download_as_string()

# some paths
path_config = json.loads(config_bucket.blob('pathConfig.json').download_as_string())
model_bucket = path_config['model_bucket']
cloud_model_path = path_config['model_path']
data_bucket = path_config['data_bucket']
cloud_data_path = path_config['data_path']
project_id = path_config['project_id']

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, 'model_refresh_requests')

users = sorted(list({
    blob.name.replace(cloud_model_path, '').split('/')[0]
    for blob in client.list_blobs(model_bucket, prefix=cloud_model_path)
}))
print('Models exist for users:\n{}'.format(users))

defaulturl = 'https://www.reddit.com/r/toronto/comments/hkjyjn/city_issues_trespassing_orders_to_demonstrators/fwt4ifw'


def model_last_updated(username: str) -> Optional[str]:
    for blob in client.list_blobs(model_bucket, prefix=os.path.join(cloud_model_path, username)):
        return blob.updated.strftime('%c')
    return None


def is_invalid(username: str, r: Reddit) -> bool:
    if len(username) == 0:
        # not catched by NotFound (as of 2020-11-04
        return True
    try:
        r.redditor(name=username).id
    except NotFound:
        return True
    return False


@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        username = request.form['requestedusername']
        if is_invalid(username, reddit):
            flash('User: {} is invalid or not found!'.format(username))
            return redirect(url_for('index'))
        else:
            return redirect(url_for('infer', username=username))
    return render_template('index.html')


@app.route('/infer/<username>', methods=('GET', 'POST'))
def infer(username):
    userresponse = {'username': username, 'defaulturl': defaulturl, 'lastupdated': model_last_updated(username)}
    if username not in users:
        flash('No model found for User: {}. Request model training?'.format(username))
        return redirect(url_for('refresh', username=username))
    refresh_local_models(username)
    if request.method == 'POST':
        print(request.form)
        url = request.form['url']
        url = url if 'reddit.com' in url else defaulturl
        sim_output = simulate_redditor_response(username, url)
        sim_output.update({
            'username': username,
            'url': url,
        })
        userresponse.update(sim_output)
    return render_template('infer.html', userinference=userresponse)


@app.route('/refresh/<username>', methods=('GET', 'POST'))
def refresh(username):
    if is_invalid(username, reddit):
        flash('User: {} is invalid or not found!'.format(username))
        return redirect(url_for('index'))
    userrefresh = {'username': username}
    if request.method == 'POST':
        future = publisher.publish(topic_path, str.encode(username))
        message_id = future.result()
        flash('Submitted request to refresh User: {}. Published Message ID: {}'.format(username, message_id))
        return redirect(url_for('index'))
    return render_template('refresh.html', userrefresh=userrefresh)
