"""TUI onboarding view — guides user through API token setup."""

from __future__ import annotations

import pytermgui as ptg

from tuidoist.api.client import AuthError, NetworkError, validate_token
from tuidoist.config.config import Config, save
from tuidoist.ui import keybindings as kb


def show_onboarding(manager: ptg.WindowManager) -> None:
    """Display the onboarding window for API token entry."""

    token_field = ptg.InputField(prompt="API Token: ")
    status_label = ptg.Label("")

    def on_submit(*_args: object) -> None:
        token = token_field.value.strip()
        if not token:
            status_label.value = "[bold 210]Please enter your API token.[/bold 210]"
            return

        status_label.value = "[bold 243]Validating token...[/bold 243]"

        try:
            validate_token(token)
        except AuthError:
            status_label.value = "[bold 210]Invalid token. Please try again.[/bold 210]"
            return
        except NetworkError as e:
            status_label.value = f"[bold 210]{e}[/bold 210]"
            return

        config = Config(api_token=token)
        save(config)

        from tuidoist.ui.views.today import show_today

        manager.remove(window)
        show_today(manager, token)

    window = ptg.Window(
        "",
        ptg.Label("[bold 183]Welcome to Tuidoist[/bold 183]"),
        "",
        ptg.Label("Enter your Todoist API token to get started."),
        ptg.Label("[243]Find it at: Settings → Integrations → Developer[/243]"),
        "",
        token_field,
        "",
        ptg.Button("Connect", onclick=on_submit),
        "",
        status_label,
        "",
        ptg.Label("[243]Esc to quit[/243]"),
        box_type=ptg.boxes.DOUBLE,
        is_modal=True,
        overflow=ptg.Overflow.SCROLL,
    )
    window.relative_width = 0.5
    window.center()
    manager.bind(kb.BACK, lambda *_: manager.stop())
    manager.bind(kb.SELECT, lambda *_: on_submit())
    manager.add(window)
