# https://www.digitalocean.com/community/tutorials/how-to-make-a-web-application-using-flask-in-python-3

from flask import Flask, render_template, request
from google.cloud import storage

from astroturf.infer import (get_qa_string, get_text_generation_pipeline,
                             make_package_infer_url)
from main import refresh_local_models
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
    txtgen = get_text_generation_pipeline(local_model_path_user_d[username])
    
    if request.method == 'POST':
        url = request.form['url']
        url = url if 'reddit.com' in url else defaulturl
        package = make_package_infer_url(url, reddit)
        prompt = get_qa_string(package)
        responses = txtgen(prompt, max_length=len(prompt.split(' '))+128)
        response = responses[0]['generated_text'].replace(prompt, '').strip().split('\n')[0]
        userresponse = {
            'username': username,
            'url': url,
            'prompt': prompt,
            'response': response,
        }
    return render_template('user.html', userresponse=userresponse)
