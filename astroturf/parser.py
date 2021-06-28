from typing import Optional


def find_username(s: str) -> Optional[str]:
    """Return {username} when given string of form * u/{username} *.
    """
    s = s.lower()
    username = None
    if 'https://www.reddit.com/u/' in s:
        # https://www.reddit.com/u/{username}/
        prefix = 'https://www.reddit.com/u/'
        username = s[s.find(prefix) + len(prefix):].split('/')[0]
    else:
        # <whitespace> u/{username} <whitespace>
        # <whitespace> /u/{username} <whitespace>
        found = False
        for word in s.split():
            if found:
                break
            for prefix in ['u/', '/u/']:
                if word.startswith(prefix):
                    username = word.replace(prefix, '')
                    found = True
                    break
    if username is not None:
        return username.strip()
