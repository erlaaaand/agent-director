from __future__ import annotations

from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.core.entities import CreativeDocumentBatch, ScriptDocumentBatch
from src.interfaces.cli_components.theme import console


def print_header() -> None:
    title = Text()
    title.append("🎬  Agent Director", style="header")
    title.append("   — Interactive Script Generator", style="subheader")
    console.print()
    console.print(Panel(str(title), border_style="blue", padding=(0, 2)))


def print_goodbye() -> None:
    console.print()
    console.print(
        Panel.fit(
            "[header]✦  Session ended. Happy creating![/header]",
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


def print_no_files() -> None:
    console.print()
    console.print(
        Panel(
            "[warning]⚠  Tidak ada file JSON ditemukan di folder input.[/warning]\n"
            "[hint]Taruh file output dari agent_market_intelligence ke folder data/input/\n"
            "Struktur yang didukung: data/input/<REGION>/<TANGGAL>/file.json[/hint]",
            border_style="yellow",
            title="[warning]Folder Input Kosong[/warning]",
            padding=(0, 2),
        )
    )
    console.print()


def print_file_preview(batch: CreativeDocumentBatch, filename: str) -> None:
    console.print()
    total = len(batch.documents)

    tbl = Table(
        title=(
            f"[header]Preview File[/header]  "
            f"[filename]{filename}[/filename]  "
            f"[subheader]· Region: {batch.region} · Tanggal: {batch.date} · {total} topik[/subheader]"
        ),
        box=box.ROUNDED,
        border_style="blue",
        header_style="bold cyan",
        show_lines=True,
        expand=True,
        padding=(0, 1),
    )

    tbl.add_column("#", style="number", justify="right", width=3, no_wrap=True)
    tbl.add_column("Document ID", style="subheader", width=22, no_wrap=True)
    tbl.add_column("Topik", style="topic", min_width=20)
    tbl.add_column("Kategori", style="category", min_width=18)
    tbl.add_column("Momentum", justify="center", width=10)
    tbl.add_column("Lifecycle", justify="center", width=12)

    for i, doc in enumerate(batch.documents, start=1):
        ti = doc.trend_identity
        metrics = ti.metrics

        momentum = metrics.get("momentum_score", "-")
        momentum_str = f"{float(momentum):.1f}" if isinstance(momentum, (int, float)) else str(momentum)

        lifecycle = metrics.get("lifecycle_stage", "-")
        lifecycle_style_map = {
            "Peak": "bold red",
            "Trending": "bold bright_green",
            "Emerging": "bold green",
            "Stagnant": "yellow",
            "Declining": "dim red",
        }
        lifecycle_style = lifecycle_style_map.get(str(lifecycle), "subheader")

        doc_id_short = doc.document_id[:20] + ("…" if len(doc.document_id) > 20 else "")

        tbl.add_row(
            str(i),
            doc_id_short,
            ti.topic,
            ti.category,
            Text(momentum_str, justify="center"),
            Text(str(lifecycle), style=lifecycle_style, justify="center"),
        )

    console.print(tbl)
    console.print()


def print_results(batches: list[ScriptDocumentBatch]) -> None:
    if not batches:
        console.print()
        console.print(
            Panel(
                "[warning]⚠  Tidak ada skrip yang berhasil dibuat.[/warning]",
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