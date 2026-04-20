from __future__ import annotations

from rich.console import Console
from rich.theme import Theme

THEME = Theme(
    {
        "header": "bold bright_cyan",
        "subheader": "dim white",
        "topic": "bold white",
        "success": "bold green",
        "error": "bold red",
        "warning": "yellow",
        "hint": "dim white",
        "number": "bold bright_blue",
        "prompt": "bold cyan",
        "hook": "magenta",
        "stat": "bold yellow",
        "menu_key": "bold green",
        "region": "bold yellow",
        "filename": "cyan",
        "category": "dim cyan",
    }
)

console = Console(theme=THEME, highlight=False)