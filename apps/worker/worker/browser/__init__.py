"""Playwright-backed browser assist helpers for application automation."""

from .auth import BrowserAuthSessionManager
from .forms import BrowserFormField, BrowserFormFillResult, GenericFormFiller
from .hooks import BrowserSiteAdapterHook, resolve_site_adapter_hook
from .service import PlaywrightBrowserAssistService, build_playwright_browser_assist_service

__all__ = [
    "BrowserAuthSessionManager",
    "BrowserFormField",
    "BrowserFormFillResult",
    "BrowserSiteAdapterHook",
    "GenericFormFiller",
    "PlaywrightBrowserAssistService",
    "build_playwright_browser_assist_service",
    "resolve_site_adapter_hook",
]
