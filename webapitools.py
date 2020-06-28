import requests

def get_entity_mentions(entity_name):
    r = requests.get('https://api.pushshift.io/reddit/search/comment/?q={qterm}'.format(
        qterm=entity_name
    ))
    return r.json()['data']
