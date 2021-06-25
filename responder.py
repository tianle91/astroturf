import os
import sqlite3
from time import sleep
from typing import Dict

import pandas as pd
from praw.objector import RedditAPIException
from praw.reddit import Reddit, Redditor
from transformers import pipeline

from astroturf.finetune import get_qa_string
from astroturf.infer import (get_text_generation_pipeline,
                             make_package_infer_url)
from astroturf.prawtools import get_reddit

reply_template = """
This was triggered by your [comment]({triggering_comment_url}).
In response to [this]({url}),
[u/{username}](https://reddit-user-analyser.netlify.app/#{username}) might reply:

{response}

---
I'm a DistilGPT2 model finetuned with user comments using 
[Huggingface's Transformers](https://github.com/huggingface/transformers).
Source code at [tianle91/astroturf](https://github.com/tianle91/astroturf).
"""


def format_reply(username: str, response: str, permalink: str, triggering_comment_url: str) -> str:
    quoted_response = '\n'.join(['> ' + s for s in response.split('\n')])
    return reply_template.format(
        username=username,
        url='https://www.reddit.com' + permalink,
        response=quoted_response,
        triggering_comment_url=triggering_comment_url
    )


def simulate_pipeline_response(
        pipeline: pipeline, permalink: str, reddit: Reddit) -> Dict[str, str]:
    url = 'https://www.reddit.com' + permalink
    package_infer = make_package_infer_url(url, reddit)
    prompt = get_qa_string(package_infer)
    response_length = 128
    responses = pipeline(
        prompt, max_length=len(prompt.split(' ')) + response_length)
    return {
        'prompt': prompt,
        'response': responses[0]['generated_text'].replace(prompt, '').strip()
    }


if __name__ == '__main__':

    reddit = get_reddit()
    db_name = 'requests.db'
    table_name = 'comments'
    model_prefix = 'model/user'

    sleep(3)

    while True:
        with sqlite3.connect(db_name) as conn:
            todo = pd.read_sql(f'''
            SELECT DISTINCT
                author,
                permalink,
                target_username,
                target_permalink
            FROM {table_name} 
            WHERE done_scraping > 0
                AND done_training > 0
                AND done_responding <= 0
            ''', conn)
        if len(todo) > 0:
            for target_username, subdf in todo.groupby(by='target_username'):
                local_model_path_user = os.path.join(
                    model_prefix, target_username, 'model')
                if os.path.isdir(local_model_path_user):
                    txtgenpipeline = get_text_generation_pipeline(
                        local_model_path_user)
                else:
                    print(f'No model found at: {local_model_path_user}')
                    txtgenpipeline = None

                for i, row in subdf.iterrows():
                    target_permalink = row['target_permalink']
                    trigger_redditor: Redditor = reddit.redditor(row['author'])
                    done = txtgenpipeline is None

                    if not done:
                        try:
                            inferresponse = simulate_pipeline_response(
                                txtgenpipeline, permalink=target_permalink, reddit=reddit)
                            reply_text = format_reply(
                                username=target_username,
                                response=inferresponse['response'],
                                permalink=target_permalink,
                                triggering_comment_url='https://www.reddit.com' +
                                subdf['permalink']
                            )
                            trigger_redditor.message(
                                subject=f'Simulated response for u/{target_username}',
                                message=reply_text
                            )
                            print(f'Messaged {trigger_redditor.name}')
                            done = True
                        except RedditAPIException as e:
                            for sube in e.items:
                                print(
                                    f'RedditAPIException. {sube.error_type}: {sube.message}')
                            print(
                                f'Did not message {trigger_redditor.name} due to exceptions')

                    if done:
                        with sqlite3.connect(db_name) as conn:
                            conn.execute(f'''
                            UPDATE {table_name}
                            SET done_responding = 1
                            WHERE author = '{row["author"]}'
                                AND permalink = '{row["permalink"]}'
                                AND target_username = '{target_username}'
                                AND target_permalink = '{target_permalink}'
                            ''')
                            conn.commit()
        else:
            sleep(1)
