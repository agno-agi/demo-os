"""Domain-locked wrappers around LLMsTxtTools for the Docs agent.

Restricts both `get_llms_txt_index` and `read_llms_txt_url` to URLs whose
hostname is in `_ALLOWED_HOSTS`. Blocks the call before any HTTP request.
"""

from urllib.parse import urlparse

from agno.tools import tool
from agno.tools.llms_txt import LLMsTxtTools

_inner = LLMsTxtTools()
_ALLOWED_HOSTS = {"docs.agno.com"}


def _is_allowed(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except (ValueError, AttributeError):
        return False
    return host in _ALLOWED_HOSTS


@tool
def get_llms_txt_index(url: str) -> str:
    """Read the LLMs.txt index from the Agno documentation.

    Args:
        url: The llms.txt index URL. Must be on docs.agno.com.
    """
    if not _is_allowed(url):
        return (
            f"Refused: {url} is not in the documentation allowlist. "
            f"Only {sorted(_ALLOWED_HOSTS)} are permitted."
        )
    return _inner.get_llms_txt_index(url)


@tool
def read_llms_txt_url(url: str) -> str:
    """Read a documentation page from the Agno documentation.

    Args:
        url: The documentation URL. Must be on docs.agno.com.
    """
    if not _is_allowed(url):
        return (
            f"Refused: {url} is not in the documentation allowlist. "
            f"Only {sorted(_ALLOWED_HOSTS)} are permitted."
        )
    return _inner.read_llms_txt_url(url)
