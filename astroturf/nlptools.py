# https://huggingface.co/transformers/usage.html#named-entity-recognition
# https://github.com/huggingface/transformers/blob/master/src/transformers/pipelines.py#L1604

from transformers import AutoTokenizer, pipeline
from transformers.pipelines import SUPPORTED_TASKS


def wrap_assert(f):
    '''sometimes i dont want to deal with exceptions in f'''
    def newf(*args,**kwargs):
        try:
            return f(*args,**kwargs)
        except Exception:
            return None
    return newf

def get_ner_tokens(s):
    # https://github.com/huggingface/transformers/blob/master/src/transformers/pipelines.py#L1681
    framework='pt'
    tokenizer = AutoTokenizer.from_pretrained(
    	SUPPORTED_TASKS['ner']["default"]["model"][framework]
    )
    return [
    	# encode -> tokens
        s for s in tokenizer.convert_ids_to_tokens(tokenizer.encode(s)) 
        if not s.startswith('[') and not s.endswith(']')
    ]

def is_hit(ner_result, entity_name_tokenized):
    ner_wordlist = [d['word'].lower() for d in ner_result]
    return all(token in ner_wordlist for token in entity_name_tokenized)

get_ner = wrap_assert(pipeline("ner"))
get_sentiment = wrap_assert(pipeline("sentiment-analysis"))
