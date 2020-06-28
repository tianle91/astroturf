# https://huggingface.co/transformers/usage.html#named-entity-recognition
# https://github.com/huggingface/transformers/blob/master/src/transformers/pipelines.py#L1604

from transformers.pipelines import SUPPORTED_TASKS
from transformers import AutoTokenizer
from transformers import pipeline

def wrap_assert(f):
    '''sometimes i dont want to deal with exceptions in f'''
    def newf(*args,**kwargs):
        try:
            return f(*args,**kwargs)
        except Exception:
            return None
    return newf

def get_ner_tokens(s):
    framework='pt'
    targeted_task = SUPPORTED_TASKS['ner']

    # https://github.com/huggingface/transformers/blob/master/src/transformers/pipelines.py#L1681
    #task_class, model_class = targeted_task["impl"], targeted_task[framework]
    model = targeted_task["default"]["model"][framework]

    tokenizer = model
    # Instantiate tokenizer if needed
    if isinstance(tokenizer, (str, tuple)):
        # if isinstance(tokenizer, tuple):
        #     # For tuple we have (tokenizer name, {kwargs})
        #     #tokenizer = AutoTokenizer.from_pretrained(tokenizer[0], **tokenizer[1])
        #     pass
        # else:
        tokenizer = AutoTokenizer.from_pretrained(tokenizer)
    
    # encode -> tokens
    return [
        s for s in tokenizer.convert_ids_to_tokens(tokenizer.encode(s)) 
        if not s.startswith('[') and not s.endswith(']')
    ]

def is_hit(ner, entity_name_tokenized):
    ner_wordlist = [d['word'].lower() for d in ner]
    return all(token in ner_wordlist for token in entity_name_tokenized)

get_ner = wrap_assert(pipeline("ner"))
get_sentiment = wrap_assert(pipeline("sentiment-analysis"))
