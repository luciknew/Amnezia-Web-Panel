"""Name normalization shared by protocol managers.

Both Telemt's `[access.users]` and the WEB proxy's MTProxy backend key users by
TOML bare keys, which only allow [A-Za-z0-9_-]. A Russian display name must
therefore survive as something readable rather than collapse into underscores.
"""

import re

_TRANSLIT = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
}


def transliterate(text):
    out = []
    for ch in text:
        low = ch.lower()
        if low in _TRANSLIT:
            mapped = _TRANSLIT[low]
            out.append(mapped.capitalize() if ch.isupper() and mapped else mapped)
        else:
            out.append(ch)
    return ''.join(out)


def is_safe_key(key):
    """True if `key` is a TOML bare key that will be read as a plain name."""
    return bool(re.fullmatch(r'[A-Za-z0-9_-]+', key or ''))
