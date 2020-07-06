import praw
from praw.exceptions import InvalidURL
from praw.models import Submission, Comment

from transformers import GPT2Tokenizer, pipeline

from data_user_comments import get_context, format_comment_as_json, format_submission_as_json
from finetune import get_qa_string

def make_package_comment(comment):
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
        return make_package_comment(refobj)
        
def get_text_generation_pipeline(modeloutputpath):
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    return pipeline('text-generation', model=modeloutputpath, tokenizer=tokenizer)

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description='ask user to respond to something.')
    parser.add_argument('--user', type=str, default='suncoasthost')
    parser.add_argument('--url', type=str, default='https://www.reddit.com/r/apple/comments/ae5cm7/apple_hires_prominent_facebook_critic_for/edn5hmg/')

    args = parser.parse_args()

    reddit = praw.Reddit()
    package = make_package_url(args.url, reddit)
    prompt = get_qa_string(package)
    print ('prompt:\n\n{}\n'.format(prompt))

    # https://huggingface.co/transformers/_modules/transformers/pipelines.html#TextGenerationPipeline
    # https://huggingface.co/transformers/_modules/transformers/modeling_utils.html#PreTrainedModel.generate
    txtgen = get_text_generation_pipeline('finetune/{}/model/'.format(args.user))
    responses = txtgen(prompt, max_length=1024)

    i = 0
    for response in responses:
        print ('response #[{}/{}]:\n\n{}'.format(
            i, len(responses), 
            responses[0]['generated_text'].replace(prompt, '').strip().split('\n')[0]
        ))
        i += 1
