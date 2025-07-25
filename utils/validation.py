import re

_LINK_RE = re.compile(
    r"(https?://|t\.me/|(?:[\w-]+\.)+[a-zA-Z]{2,})",
    flags=re.IGNORECASE,
)


def contains_link_or_mention(text: str) -> bool:
    """Return True if text contains a URL-like pattern or '@'."""
    if "@" in text:
        return True
    return bool(_LINK_RE.search(text))
