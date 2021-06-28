import re
from typing import Optional, Tuple


def parse_comment_body(s: str) -> Tuple[bool, Optional[str]]:
    """Return whether comment is relevent and mentioned username.
    """
    regex_str_username = r'(.|\s)*u/[a-zA-Z0-9_]*\s'
    regex_str_trigger = regex_str_username + r'(think|say|do)?'
    if re.match(regex_str_trigger, s, flags=re.IGNORECASE):
        return True, re.search(regex_str_username, s).group(0).split('u/')[1].strip()
    else:
        return False, None
