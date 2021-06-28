from astroturf.parser import parse_comment_body


def test_parse_comment_body():
    assert parse_comment_body('u/username ?') == (True, 'username')
    assert parse_comment_body(
        'what would u/UserName say?') == (True, 'UserName')
    assert not parse_comment_body('bullshit')[0]
