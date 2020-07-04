from transformers import GPT2Tokenizer, pipeline

def get_text_generation_pipeline(modeloutputpath):
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    return pipeline('text-generation', model=modeloutputpath, tokenizer=tokenizer)

if __name__ == '__main__':
    modeloutputpath = 'finetune/suncoasthost/model/'
    predictor = get_text_generation_pipeline(modeloutputpath)
    prompt = 'In subreddit: node\nTitle: Do you like Trump?\n\nQ: What do you think?\nA: '
    print (predictor(prompt)[0]['generated_text'])
