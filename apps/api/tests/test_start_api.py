from app.core.config import Settings
from scripts.start_api import resolve_runtime_host, resolve_runtime_port


def test_resolve_runtime_host_uses_settings_value() -> None:
    settings = Settings(api_host="127.0.0.1")

    assert resolve_runtime_host(settings) == "127.0.0.1"


def test_resolve_runtime_port_prefers_platform_port() -> None:
    settings = Settings(api_port=8000)

    assert resolve_runtime_port(settings, port_override="10000") == 10000


def test_resolve_runtime_port_falls_back_to_api_port() -> None:
    settings = Settings(api_port=8000)

    assert resolve_runtime_port(settings, port_override="") == 8000
