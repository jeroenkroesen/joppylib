"""Shared fixtures for joppylib tests"""

import pytest

from joppylib.config import Settings


@pytest.fixture
def settings():
    """A Settings instance with all defaults."""
    return Settings()


@pytest.fixture
def api_key():
    """A dummy API key for testing."""
    return "test_api_key_abc123"


@pytest.fixture
def base_url(settings):
    """The base URL derived from default settings."""
    return settings.base_url


def make_paginated_response(items, has_more=False):
    """Build a Joplin-style paginated response body.

    Parameters
    ----------
    items : list
        The items to include in this page.
    has_more : bool
        Whether more pages follow this one.

    Returns
    -------
    dict
        A dict matching the Joplin pagination format:
        {"items": [...], "has_more": bool}
    """
    return {"items": items, "has_more": has_more}
