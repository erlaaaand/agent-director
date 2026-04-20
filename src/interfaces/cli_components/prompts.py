from __future__ import annotations

import sys
from typing import Literal

from rich import box
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

from src.interfaces.cli_components.theme import console

_MainAction = Literal["file", "all", "exit"]
_FileAction = Literal["preview", "generate", "back"]


def prompt_main_menu(files: list[str]) -> tuple[_MainAction, str | None]:
    console.print()
    console.print(Rule("[bold cyan]MENU UTAMA[/bold cyan]", style="dim blue"))
    console.print()

    tbl = Table(
        box=box.SIMPLE,
        header_style="bold cyan",
        show_edge=False,
        padding=(0, 2),
    )
    tbl.add_column("No", style="number", justify="right", width=4, no_wrap=True)
    tbl.add_column("Region", style="region", width=8, no_wrap=True)
    tbl.add_column("Tanggal", style="subheader", width=12, no_wrap=True)
    tbl.add_column("File", style="filename")
    tbl.add_column("Topik", style="stat", justify="right", width=6)

    for i, f in enumerate(files, start=1):
        parts = f.replace("\\", "/").split("/")
        region = parts[0] if len(parts) >= 3 else "-"
        date = parts[1] if len(parts) >= 3 else (parts[0] if len(parts) == 2 else "-")
        fname = parts[-1]
        tbl.add_row(str(i), region, date, fname, "?")

    console.print(tbl)
    console.print()
    console.print("  [menu_key][ 1-%d ][/menu_key]  [white]Pilih file berdasarkan nomor[/white]" % len(files))
    console.print("  [menu_key][  A  ][/menu_key]  [white]Proses semua file sekaligus[/white]")
    console.print("  [menu_key][  E  ][/menu_key]  [error]Exit[/error]")
    console.print()

    while True:
        try:
            raw = console.input("[prompt]  > [/prompt]").strip().lower()
        except (KeyboardInterrupt, EOFError):
            console.print()
            return "exit", None

        if raw == "e":
            return "exit", None

        if raw == "a":
            return "all", None

        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(files):
                return "file", files[idx]
            console.print(
                f"[error]  Nomor tidak valid.[/error] "
                f"[hint]Masukkan 1–{len(files)}.[/hint]"
            )
            continue

        console.print(
            "[error]  Input tidak dikenal.[/error] "
            "[hint]Ketik nomor file, A, atau E.[/hint]"
        )


def prompt_file_action(filename: str) -> _FileAction:
    console.print()
    console.print(Rule(f"[bold cyan]FILE:[/bold cyan] [filename]{filename}[/filename]", style="dim blue"))
    console.print()
    console.print("  [menu_key][ P ][/menu_key]  [white]Preview isi file (topik & kategori)[/white]")
    console.print("  [menu_key][ G ][/menu_key]  [white]Generate script dengan LLM[/white]")
    console.print("  [menu_key][ B ][/menu_key]  [white]Kembali ke menu utama[/white]")
    console.print()

    valid: dict[str, _FileAction] = {"p": "preview", "g": "generate", "b": "back"}

    while True:
        try:
            raw = console.input("[prompt]  > [/prompt]").strip().lower()
        except (KeyboardInterrupt, EOFError):
            console.print()
            return "back"

        if raw in valid:
            console.print()
            return valid[raw]

        console.print(
            "[error]  Input tidak valid.[/error] "
            "[hint]Ketik P, G, atau B.[/hint]"
        )