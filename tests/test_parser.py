from astroturf.parser import parse_comment_body
import pytest


@pytest.mark.parametrize(
    ('s', 'expected_username'),
    [
        pytest.param('u/username ?', 'username'),
        pytest.param(' u/username ?', 'username'),
        pytest.param('u/username say?', 'username'),
        pytest.param('what would u/username say?', 'username'),
        pytest.param('u/username1 ?', 'username1'),
        pytest.param('u/user_name ?', 'user_name'),
    ]
)
def test_parse_comment_body_relevant(s, expected_username):
    res = parse_comment_body(s)
    assert res[0]
    actual_username = res[1]
    assert expected_username == actual_username, actual_username


@pytest.mark.parametrize(
    ('s'),
    [
        pytest.param('bullshit'),
        pytest.param('u/username?'),
    ]
)
def test_parse_comment_body_not_relevant(s):
    assert not parse_comment_body(s)[0]
