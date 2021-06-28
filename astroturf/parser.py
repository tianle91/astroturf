import re
from typing import Optional, Tuple


def parse_comment_body(s: str) -> Tuple[bool, Optional[str]]:
    """Return whether comment is relevent and mentioned username.
    """
    if re.match('.*u/[a-zA-Z0-9]*\s(think|say|do)?', s, flags=re.IGNORECASE):
        return True, re.search('u/[a-zA-Z0-9]*', s).group(0).split('u/')[1]
    else:
        return False, None
