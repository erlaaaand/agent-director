from __future__ import annotations

from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.core.entities import ScriptDocumentBatch
from src.interfaces.cli_components.theme import console


def print_header() -> None:
    title = Text()
    title.append("🎬  Agent Director", style="header")
    title.append("   — Scene-by-Scene Script Generator", style="subheader")
    console.print()
    console.print(Panel(str(title), border_style="blue", padding=(0, 2)))


def print_goodbye() -> None:
    console.print()
    console.print(
        Panel.fit(
            "[header]✦  Semua skrip berhasil dibuat. Happy creating![/header]",
            border_style="blue",
            padding=(0, 2),
        )
    )
    console.print()


def print_error(title: str, detail: str, hint: str = "") -> None:
    body = f"[error]{detail}[/error]"
    if hint:
        body += f"\n\n[hint]💡 {hint}[/hint]"
    console.print()
    console.print(
        Panel(
            body,
            title=f"[error]✗  {title}[/error]",
            border_style="red",
            padding=(0, 2),
        )
    )
    console.print()


def print_results(batches: list[ScriptDocumentBatch]) -> None:
    if not batches:
        console.print()
        console.print(
            Panel(
                "[warning]⚠  Tidak ada skrip yang berhasil dibuat.[/warning]\n"
                "[hint]Pastikan folder data/input berisi file JSON dari agent_market_intelligence.[/hint]",
                border_style="yellow",
                title="[warning]Tidak Ada Output[/warning]",
                padding=(0, 2),
            )
        )
        console.print()
        return

    total_scripts = sum(len(b.scripts) for b in batches)

    tbl = Table(
        title=(
            f"[header]Script Generation Report[/header]  "
            f"[subheader]— {total_scripts} skrip dari {len(batches)} batch[/subheader]"
        ),
        box=box.ROUNDED,
        border_style="blue",
        header_style="bold cyan",
        show_lines=True,
        expand=True,
        padding=(0, 1),
    )

    tbl.add_column("#", style="number", justify="right", width=3, no_wrap=True)
    tbl.add_column("Topik", style="topic", min_width=18)
    tbl.add_column("Judul Video", style="hook", min_width=30)
    tbl.add_column("Platform", style="subheader", width=14, no_wrap=True)
    tbl.add_column("Durasi", justify="center", width=8)
    tbl.add_column("Scenes", justify="center", width=7)
    tbl.add_column("BGM Mood", style="subheader", min_width=14)

    idx = 1
    for batch in batches:
        for script in batch.scripts:
            pm = script.production_metadata
            title_preview = script.distribution_assets.suggested_title
            if len(title_preview) > 45:
                title_preview = title_preview[:43] + "…"

            total_dur = sum(s.estimated_duration_sec for s in script.scenes)

            tbl.add_row(
                str(idx),
                script.topic,
                title_preview,
                pm.platform.split("/")[0].strip(),
                Text(f"{total_dur:.0f}s", style="stat", justify="center"),
                Text(str(len(script.scenes)), style="stat", justify="center"),
                pm.bgm_mood[:20],
            )
            idx += 1

    console.print()
    console.print(tbl)
    console.print()
    console.print(
        f"  [success]✓  {total_scripts} skrip disimpan ke data/output/[/success]"
    )
    console.print()
