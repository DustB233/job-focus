from __future__ import annotations

import argparse

from worker.browser.auth import BrowserAuthSessionManager
from worker.browser.service import default_browser_factory
from worker.config import WorkerSettings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture and save Playwright auth state for browser-assisted application mode."
    )
    parser.add_argument("--login-url", required=True, help="URL to open for interactive login.")
    parser.add_argument(
        "--state-key",
        required=True,
        help="State key to store, usually source-hostname such as manual-example.com.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    settings = WorkerSettings()
    manager = BrowserAuthSessionManager(settings.resolved_browser_auth_state_dir)

    with default_browser_factory(headless=False) as browser:
        context = browser.new_context()
        page = context.new_page()
        page.goto(args.login_url, wait_until="domcontentloaded")
        input("Complete login in the browser, then press Enter to save auth state...")
        saved_path = manager.save_context_state(context, args.state_key)
        print(f"Saved auth state to {saved_path}")
        close = getattr(context, "close", None)
        if callable(close):
            close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
