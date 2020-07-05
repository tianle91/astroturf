from transformers import GPT2Tokenizer, pipeline

def get_text_generation_pipeline(modeloutputpath):
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    return pipeline('text-generation', model=modeloutputpath, tokenizer=tokenizer)

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description='ask user if they like trump.')
    parser.add_argument('--user', type=str, default='suncoasthost')
    args = parser.parse_args()

    modeloutputpath = 'finetune/{}/model/'.format(args.user)
    predictor = get_text_generation_pipeline(modeloutputpath)
    prompt = 'In subreddit: node\nTitle: Do you like Trump?\n\nQ: What do you think?\nA: '
    print (predictor(prompt)[0]['generated_text'])
