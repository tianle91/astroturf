import os
import json
import pandas as pd

from webapitools import get_entity_mentions
from nlptools import get_ner_tokens, get_ner, get_sentiment, is_hit
from datetime import datetime

def clean_string(s):
    return ''.join([c if c.isalnum() else '_' for c in s])

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description='search comments for entity, run ner and sentiment if hit.')
    parser.add_argument('--entity', type=str, default='uber')
    parser.add_argument('--size', type=int, default=500)
    args = parser.parse_args()
    
    entity_name = args.entity
    size = args.size

    outpath = 'data/search/comment/q={}'.format(clean_string(entity_name))
    os.makedirs(outpath, exist_ok=True)

    manifestpath = os.path.join(outpath, 'manifest.csv')
    if not os.path.isfile(manifestpath):
        with open(manifestpath, 'w+') as f:
            f.write('query, created_utcnow_isoformat\n')
        manifestdf = None
    else:
        manifestdf = pd.read_csv(manifestpath)

    comments = get_entity_mentions(entity_name, size=size)
    utciso = datetime.utcnow().isoformat()
    entity_name_tokenized = get_ner_tokens(entity_name)

    comments_hit = []
    for comment in comments:
        ner = get_ner(comment['body'])
        comment_id = comment['id']
        if is_hit(ner, entity_name_tokenized):
            comment.update({'sentiment': get_sentiment(comment['body'])})
            comment_outfname = os.path.join(outpath, '{}.json'.format(comment_id))
            if not os.path.isfile(comment_outfname):
                with open(comment_outfname, 'w+') as f:
                    json.dump(comments_hit, f, indent=4)

    with open(manifestpath, 'a+') as f:
        f.write('{query}, {utciso}\n'.format(
            query=entity_name,
            utciso=utciso, 
        ))

    # get_ipython().system('gsutil -m rsync -r data/search/comment gs://astroturf-dev/search/comment')
