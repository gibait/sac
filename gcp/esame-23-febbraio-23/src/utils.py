import re

def get_hashtags(msg: str) -> list:
    return re.findall('(#\w+)', msg, re.DOTALL)