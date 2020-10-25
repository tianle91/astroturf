# https://www.digitalocean.com/community/tutorials/how-to-make-a-web-application-using-flask-in-python-3

from flask import Flask, render_template, request
from google.cloud import storage

from astroturf.infer import (get_qa_string, get_text_generation_pipeline,
                             make_package_infer_url)
from main import refresh_local_models, simulate_redditor_response
from praw_utils import get_reddit

app = Flask(__name__)
client = storage.Client()
reddit = get_reddit(client, 'astroturf-dev-configs')

with open('users.txt') as f:
    users = f.read().split()

local_model_path_user_d = {
    user_name: refresh_local_models(user_name)
    for user_name in users
}

defaulturl = 'https://www.reddit.com/r/toronto/comments/hkjyjn/city_issues_trespassing_orders_to_demonstrators/fwt4ifw'

@app.route('/')
def index():
    return render_template('index.html', users=[{'username': s} for s in users])

@app.route('/<username>', methods=('GET', 'POST'))
def user(username):
    userresponse = {'username': username, 'defaulturl': defaulturl}
    if request.method == 'POST':
        url = request.form['url']
        url = url if 'reddit.com' in url else defaulturl
        sim_output = simulate_redditor_response(username, url)
        sim_output.update({
            'username': username,
            'url': url,
        })
        userresponse.update(sim_output)
    return render_template('user.html', userresponse=userresponse)
