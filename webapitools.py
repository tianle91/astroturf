import requests

def get_entity_mentions(entity_name, size=None):
	q = 'https://api.pushshift.io/reddit/search/comment/?q={qterm}&size={size}'.format(
		qterm=entity_name,
		size=size if size is not None else 25
	)
    return requests.get(q).json()['data']
