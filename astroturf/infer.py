from praw.exceptions import InvalidURL
from praw.models import Submission, Comment

from transformers import GPT2Tokenizer, pipeline

from astroturf.finetune import get_qa_string
from astroturf.prawtools import get_context, format_comment_as_json, format_submission_as_json

def make_package_comment(comment, reddit):
    _, submission = get_context(comment, reddit)
    return {
        'comment': None,
        'parent_comment': format_comment_as_json(comment),
        'submission': format_submission_as_json(submission)
    }

def make_package_submission(submission):
    return {
        'comment': None,
        'parent_comment': None,
        'submission': format_submission_as_json(submission)
    }

def make_package_url(url, reddit):
    try:
        refobj = reddit.comment(url=url)
    except InvalidURL:
        refobj = reddit.submission(url=url)

    if isinstance(refobj, Submission):
        return make_package_submission(refobj)
    elif isinstance(refobj, Comment):
        return make_package_comment(refobj, reddit)
        
def get_text_generation_pipeline(modeloutputpath):
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    return pipeline('text-generation', model=modeloutputpath, tokenizer=tokenizer)
