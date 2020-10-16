# https://huggingface.co/transformers/quickstart.html
# https://github.com/huggingface/transformers/tree/master/examples/language-modeling
# https://github.com/huggingface/transformers/blob/master/examples/language-modeling/run_language_modeling.py
# https://github.com/huggingface/transformers/blob/master/src/transformers/training_args.py

import json
import os
from glob import glob

import numpy as np
from transformers import (DataCollatorForLanguageModeling, GPT2LMHeadModel,
                          GPT2Tokenizer, PreTrainedTokenizer, TextDataset,
                          Trainer, TrainingArguments)

tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2")
eos = tokenizer.eos_token

# data part

def get_qa_string(package):
    '''format comment as question and answer'''
    context = 'In subreddit: {subname}\nTitle: {title}\n{body}'.format(
        subname = package['submission']['subreddit'],
        title = package['submission']['title'],
        body = package['submission']['selftext'],
    )
    question = 'What do you think?'
    if package['parent_comment'] is not None:
        question = package['parent_comment']['body']
    return '{context}\n\nQ: {q}\nA: {a}'.format(
        context = context,
        q = question,
        a = package['comment']['body'] if package['comment'] is not None else '',
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
            package = json.load(f)
        with open(outputfname, 'a+') as f:
            f.write('{body}\n{eos}\n'.format(
                body=get_qa_string(package),
                eos=eos
            ))

# training part

def get_dataset(file_path, tokenizer: PreTrainedTokenizer, block_size: int=None):
    return TextDataset(
        tokenizer = tokenizer, 
        file_path = file_path, 
        block_size = block_size if block_size is not None else tokenizer.max_len,
        overwrite_cache = True,
    )

def dump_finetuned(inputpath, outputpath, blocksize=16, max_steps=50):
    '''Finetune GPT2LMHeadModel
    inputpath: expect .json here as outputs of astroturf.prawtools.make_package_training
    outputpath: to dump finetuned huggingface transformers
    blocksize:
    '''
    print('blocksize: {}, max_steps: {}'.format(blocksize, max_steps))
    print('inputpath: {}'.format(inputpath))
    print('outputpath: {}'.format(outputpath))

    # model data

    fnames = glob(os.path.join(inputpath, '*.json'))
    assert len(fnames) > 0, 'check inputpath: {} is not empty!'.format(inputpath)
    valid_prop = .1
    shuffled_indices = list(np.random.choice(range(len(fnames)), len(fnames), replace=False))
    valid_size = max(1, int(valid_prop*len(fnames)))

    fnames_shuffled = [fnames[i] for i in shuffled_indices]
    fnames_test = fnames_shuffled[:valid_size]
    fnames_valid = fnames_shuffled[valid_size:2*valid_size]
    fnames_train = fnames_shuffled[2*valid_size:]

    modeldatapath = os.path.join(outputpath, 'data')
    os.makedirs(modeldatapath, exist_ok=True)

    file_path_train = os.path.join(modeldatapath, 'train.txt')
    file_path_valid = os.path.join(modeldatapath, 'valid.txt')
    file_path_test = os.path.join(modeldatapath, 'test.txt')

    write_to_text(fnames_train, file_path_train)
    write_to_text(fnames_valid, file_path_valid)
    write_to_text(fnames_test, file_path_test)

    # model training

    train_dataset = get_dataset(file_path_train, tokenizer=tokenizer, block_size=blocksize)
    valid_dataset = get_dataset(file_path_valid, tokenizer=tokenizer, block_size=blocksize)
    test_dataset = get_dataset(file_path_test, tokenizer=tokenizer, block_size=blocksize)

    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    modeloutputpath = os.path.join(outputpath, 'model')
    training_args = TrainingArguments(
        output_dir=modeloutputpath,
        do_train=True,
        do_eval=True,
        evaluate_during_training=True,
        learning_rate=1e-4,
        max_steps=max_steps,
        save_total_limit=0,
        # logging_dir='./log',
        # logging_first_step=True,
        logging_steps=10,
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
    return True
