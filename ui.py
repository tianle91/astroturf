# https://www.digitalocean.com/community/tutorials/how-to-make-a-web-application-using-flask-in-python-3

import json

from flask import Flask, render_template, request, flash, redirect, url_for
from google.cloud import pubsub_v1
from google.cloud import storage

from main import refresh_local_models, simulate_redditor_response, is_invalid, is_trained, model_last_updated
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
    if not is_trained(username):
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
