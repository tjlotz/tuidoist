"""Tuidoist TUI application entry point."""

from __future__ import annotations

import sys
import traceback
from typing import Any

import pytermgui as ptg

from tuidoist.config.config import load
from tuidoist.ui.views.onboarding import show_onboarding
from tuidoist.ui.views.today import show_today


def _patch_terminal_resize() -> None:
    """Work around pytermgui reentrant resize crash on Python 3.14+.

    The default _update_size calls hasattr(self, "resolution") which triggers
    the cached_property, which calls getch, which re-enters _update_size.
    This patch skips the resolution invalidation entirely.
    """

    def _safe_update_size(self: Any, *_: Any) -> None:
        try:
            del self.__dict__["resolution"]
        except KeyError:
            pass

        self.size = self._get_size()
        self._call_listener(self.RESIZE, self.size)
        self.write("\x1b[2J")

    ptg.Terminal._update_size = _safe_update_size  # type: ignore[assignment]


def main() -> None:
    """Launch the Tuidoist TUI."""
    _patch_terminal_resize()
    config = load()

    try:
        with ptg.WindowManager() as manager:
            # Define a single full-screen slot for the main content
            manager.layout.add_slot("main", width=1.0, height=1.0)

            if config.is_authenticated:
                show_today(manager, config.api_token)
            else:
                show_onboarding(manager)
    except Exception:
        # Manager context has exited and restored the normal screen, so it's
        # safe to print a traceback. Without this, any unexpected exception
        # in the event loop would exit silently and look like a crash.
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
