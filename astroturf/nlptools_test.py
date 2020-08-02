from astroturf.nlptools import get_ner, get_ner_tokens, is_hit

def test_get_ner_tokens():
    assert get_ner_tokens('uber') == ['u', '##ber'], 'failed get_ner_tokens'

def test_is_hit():
    res = is_hit(
        ner_result=get_ner('I love taking Uber around the city!'), 
        entity_name_tokenized=['u', '##ber']
    )
    assert res, 'failed is_hit'
