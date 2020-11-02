# https://www.digitalocean.com/community/tutorials/how-to-make-a-web-application-using-flask-in-python-3

import json
import os
from typing import Optional

from flask import Flask, render_template, request
from google.cloud import storage

from main import refresh_local_models, simulate_redditor_response
from praw_utils import get_reddit

app = Flask(__name__)
client = storage.Client()
reddit = get_reddit(client, 'astroturf-dev-configs')
client = storage.Client()
config_bucket = client.bucket('astroturf-dev-configs')
path_config = json.loads(config_bucket.blob('pathConfig.json').download_as_string())
model_bucket = path_config['model_bucket']
cloud_model_path = path_config['model_path']
data_bucket = path_config['data_bucket']
cloud_data_path = path_config['data_path']

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


def data_last_updated(username: str) -> Optional[str]:
    maxdate = None
    for blob in client.list_blobs(data_bucket, prefix=os.path.join(cloud_data_path, username)):
        if maxdate is None or blob.updated > maxdate:
            maxdate = blob.updated
    return maxdate.strftime('%c')


@app.route('/')
def index():
    return render_template('index.html', users=[{'username': s} for s in users])


@app.route('/<username>', methods=('GET', 'POST'))
def user(username):
    userresponse = {'username': username, 'defaulturl': defaulturl, 'lastupdated': model_last_updated(username)}
    # (premature?) optimization for simulate_redditor_response
    refresh_local_models(username)
    if request.method == 'POST':
        print (request.form)
        url = request.form['url']
        url = url if 'reddit.com' in url else defaulturl
        sim_output = simulate_redditor_response(username, url)
        sim_output.update({
            'username': username,
            'url': url,
        })
        userresponse.update(sim_output)
    return render_template('user.html', userinference=userresponse)


@app.route('/<username>/refresh', methods=('GET', 'POST'))
def refresh(username):
    userrefresh = {
        'username': username,
        'modellastupdated': model_last_updated(username),
        'datalastupdated': data_last_updated(username)
    }
    if request.method == 'POST':
        if 'update_data' in request.form:
            print ('TODO: publish request to update data')
        if 'update_model' in request.form:
            print('TODO: publish request to update model')
    return render_template('refresh.html', userrefresh=userrefresh)
