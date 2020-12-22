from praw import Reddit
from praw.exceptions import InvalidURL
from praw.models import Comment, Submission
from transformers import GPT2Tokenizer, pipeline

from astroturf.prawtools import (make_package_infer_comment,
                                 make_package_infer_submission)


def make_package_infer_url(url: str, reddit: Reddit) -> dict:
    """Return package like astroturf.prawtools.make_package_training but for inference.

    Args:
        url (str): url for inference
        reddit (Reddit): ...
    """
    try:
        refobj = reddit.comment(url=url)
    except InvalidURL:
        refobj = reddit.submission(url=url)

    if isinstance(refobj, Submission):
        return make_package_infer_submission(refobj)
    elif isinstance(refobj, Comment):
        return make_package_infer_comment(refobj, reddit)


def get_text_generation_pipeline(modeloutputpath) -> pipeline:
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    return pipeline('text-generation', model=modeloutputpath, tokenizer=tokenizer)
