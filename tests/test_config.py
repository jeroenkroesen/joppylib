"""Tests for joppylib.config — Settings and computed fields"""

from joppylib.config import Settings


class TestSettingsDefaults:
    """Verify that Settings() produces the expected Joplin defaults."""

    def test_protocol(self, settings):
        assert settings.protocol == "http://"

    def test_host(self, settings):
        assert settings.host == "localhost"

    def test_port(self, settings):
        assert settings.port == "41184"

    def test_pagesize(self, settings):
        assert settings.pagesize == 100

    def test_ping_route(self, settings):
        assert settings.ping_route == "ping"

    def test_auth_init_route(self, settings):
        assert settings.auth_init_route == "auth"

    def test_auth_check_route(self, settings):
        assert settings.auth_check_route == "auth/check"

    def test_search_route(self, settings):
        assert settings.search_route == "search"


class TestBaseUrl:
    """Verify the computed base_url field."""

    def test_default_base_url(self, settings):
        assert settings.base_url == "http://localhost:41184"

    def test_custom_base_url(self):
        s = Settings(protocol="https://", host="myhost", port="8080")
        assert s.base_url == "https://myhost:8080"
