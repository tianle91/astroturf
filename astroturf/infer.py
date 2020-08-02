from praw.exceptions import InvalidURL
from praw.models import Comment, Submission
from transformers import GPT2Tokenizer, pipeline

from astroturf.finetune import get_qa_string
from astroturf.prawtools import (format_comment_as_json,
                                 format_submission_as_json, get_context,
                                 make_package_infer_comment,
                                 make_package_infer_submission)


def make_package_infer_url(url, reddit):
    try:
        refobj = reddit.comment(url=url)
    except InvalidURL:
        refobj = reddit.submission(url=url)

    if isinstance(refobj, Submission):
        return make_package_infer_submission(refobj)
    elif isinstance(refobj, Comment):
        return make_package_infer_comment(refobj, reddit)
        
def get_text_generation_pipeline(modeloutputpath):
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    return pipeline('text-generation', model=modeloutputpath, tokenizer=tokenizer)
