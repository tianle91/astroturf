# https://www.digitalocean.com/community/tutorials/how-to-make-a-web-application-using-flask-in-python-3

import praw
from glob import glob
from flask import Flask, render_template, request

from infertools import make_package_url, get_qa_string, get_text_generation_pipeline

app = Flask(__name__)
reddit = praw.Reddit()

username_l = [
    s.replace('finetune/', '').replace('/model/pytorch_model.bin', '') 
    for s in glob('finetune/*/model/pytorch_model.bin')
]

@app.route('/')
def index():
    users = [{'username': username} for username in username_l]
    return render_template('index.html', users=users)

@app.route('/<username>', methods=('GET', 'POST'))
def user(username):
    userresponse = {'username': username}
    txtgen = get_text_generation_pipeline('finetune/{}/model/'.format(username))
    
    if request.method == 'POST':
        url = request.form['url']
        package = make_package_url(url, reddit)
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
