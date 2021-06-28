import pytest

from astroturf.parser import find_username


@pytest.mark.parametrize(
    ('s', 'expected_username'),
    [
        pytest.param('u/username ?', 'username'),
        pytest.param('u/username1 ?', 'username1'),
        pytest.param('u/userName ?', 'username'),
        pytest.param('u/user_name ?', 'user_name'),
        pytest.param(' u/username ?', 'username'),
        pytest.param('u/username say?', 'username'),
        pytest.param('what would u/username say?', 'username'),
        pytest.param('what would u/user_name say?', 'user_name'),
        pytest.param('https://www.reddit.com/u/username/', 'username'),
        pytest.param('(https://www.reddit.com/u/username/)', 'username'),
        pytest.param('www.site.edu/page', None)
    ]
)
def test_find_username(s, expected_username):
    res = find_username(s)
    if expected_username is not None:
        assert expected_username == res, res
    else:
        assert expected_username is None
