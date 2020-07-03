# https://huggingface.co/transformers/quickstart.html
# https://github.com/huggingface/transformers/tree/master/examples/language-modeling
# https://github.com/huggingface/transformers/blob/master/examples/language-modeling/run_language_modeling.py
# https://github.com/huggingface/transformers/blob/master/src/transformers/training_args.py

import os
import json
from glob import glob
import numpy as np
from transformers import (
    GPT2Tokenizer, 
    GPT2LMHeadModel, 
    TextDataset, 
    PreTrainedTokenizer, 
    DataCollatorForLanguageModeling,
    TrainingArguments, 
    Trainer
)

# data part

def get_qa_string(comment):
    '''format comment as question and answer'''
    context = 'In subreddit: {subname}\nTitle: {title}\n{body}'.format(
        subname = comment['submission']['subreddit'],
        title = comment['submission']['title'],
        body = comment['submission']['selftext'],
    )
    question = 'What do you think?'
    if comment['parent_comment'] is not None:
        question = comment['parent_comment']['body']
    return '{context}\n\nQ: {q}\nA: {a}'.format(
        context = context,
        q = question,
        a = comment['comment']['body'],
    )

def write_to_text(fnames, outputfname, verbose=1):
    # clear destination
    with open(outputfname, 'w+') as f:
        f.write('')
    
    total = len(fnames)
    i = 0
    for fname in fnames:
        if i % 100 == 0 and verbose > 0:
            print ('[{}/{}]'.format(i, total))
        i += 1
        with open(fname) as f:
            comment = json.load(f)
        with open(outputfname, 'a+') as f:
            f.write('{body}\n{eos}\n'.format(
                body=get_qa_string(comment),
                eos=eos
            ))

# training part

def get_dataset(file_path, tokenizer: PreTrainedTokenizer):
    return TextDataset(
        tokenizer=tokenizer, 
        file_path=file_path, 
        #block_size=tokenizer.max_len, 
        block_size=128,
        overwrite_cache=True,
    )

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description='finetune on user comments.')
    parser.add_argument('--input', type=str, default='data/user/suncoasthost')
    parser.add_argument('--output', type=str, default='finetune/suncoasthost')
    args = parser.parse_args()

    gpt2pretrainedstr = "gpt2"
    tokenizer = GPT2Tokenizer.from_pretrained(gpt2pretrainedstr)
    model = GPT2LMHeadModel.from_pretrained(gpt2pretrainedstr)
    eos = tokenizer.eos_token

    # model data

    fnames = glob(os.path.join(args.inputpath, '*.json'))
    valid_prop = .1
    shuffled_indices = list(np.random.choice(range(len(fnames)), len(fnames), replace=False))
    valid_size = max(1, int(valid_prop*len(fnames)))

    fnames_shuffled = [fnames[i] for i in shuffled_indices]
    fnames_test = fnames_shuffled[:valid_size]
    fnames_valid = fnames_shuffled[valid_size:2*valid_size]
    fnames_train = fnames_shuffled[2*valid_size:]

    modeldatapath = os.path.join(args.output, 'data')
    os.makedirs(modeldatapath, exist_ok=True)

    file_path_train = os.path.join(modeldatapath, 'train.txt')
    file_path_valid = os.path.join(modeldatapath, 'valid.txt')
    file_path_test = os.path.join(modeldatapath, 'test.txt')

    write_to_text(fnames_train, file_path_train)
    write_to_text(fnames_valid, file_path_valid)
    write_to_text(fnames_test, file_path_test)

    # model training

    train_dataset = get_dataset(file_path_train, tokenizer=tokenizer)
    valid_dataset = get_dataset(file_path_valid, tokenizer=tokenizer)
    test_dataset = get_dataset(file_path_test, tokenizer=tokenizer)

    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    modeloutputpath = os.path.join(args.output, 'model')

    training_args = TrainingArguments(
        output_dir=modeloutputpath,
        do_train=True,
        do_eval=True,
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        prediction_loss_only=True,
    )
    trainer.train()
    trainer.save_model()
    print (trainer.evaluate())
