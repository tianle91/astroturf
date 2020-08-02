import praw

from astroturf.infer import (get_qa_string, get_text_generation_pipeline,
                             make_package_infer_url)

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description='ask user to respond to something.')
    parser.add_argument('--user', type=str, default='suncoasthost')
    parser.add_argument('--url', type=str, default='https://www.reddit.com/r/apple/comments/ae5cm7/apple_hires_prominent_facebook_critic_for/edn5hmg/')

    args = parser.parse_args()

    reddit = praw.Reddit()
    package = make_package_infer_url(args.url, reddit)
    prompt = get_qa_string(package)
    print ('prompt:\n\n{}\n'.format(prompt))

    # https://huggingface.co/transformers/_modules/transformers/pipelines.html#TextGenerationPipeline
    # https://huggingface.co/transformers/_modules/transformers/modeling_utils.html#PreTrainedModel.generate
    txtgen = get_text_generation_pipeline('finetune/{}/model/'.format(args.user))
    responses = txtgen(prompt, max_length=len(prompt.split(' '))+128, num_return_sequences=10)

    i = 0
    for response in responses:
        print ('response #[{}/{}]:\n\n{}'.format(
            i, len(responses), 
            response['generated_text'].replace(prompt, '').strip().split('\n')[0]
        ))
        i += 1
