import re
from typing import Optional


U_NAME_DETECTOR = re.compile(r'u/[a-z0-9_-]*')


def find_username(s: str) -> Optional[str]:
    u_name_results = U_NAME_DETECTOR.search(s.lower())
    if u_name_results is not None:
        return u_name_results.group().split('u/')[1]
