from __future__ import annotations

import argparse
import logging

from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from src.application.director_use_case import DirectorUseCase
from src.core.exceptions import AgentDirectorError, LLMGenerationError, StorageError
from src.interfaces.cli_components.display import (
    print_error,
    print_goodbye,
    print_header,
    print_results,
)
from src.interfaces.cli_components.theme import console

logger = logging.getLogger(__name__)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent_director",
        description="Generate TikTok/Shorts scripts from market intelligence JSON files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py                # proses semua file di data/input/\n"
        ),
    )
    return parser


def run_cli(use_case: DirectorUseCase) -> None:
    build_arg_parser().parse_args()
    print_header()

    try:
        with Progress(
            SpinnerColumn(spinner_name="dots", style="cyan"),
            TextColumn("[white]Generating scripts…[/white]"),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("", total=None)
            batches = use_case.execute()
            progress.stop_task(task)

        print_results(batches)
        print_goodbye()

    except StorageError as exc:
        print_error(
            title="Storage Error",
            detail=exc.message,
            hint="Pastikan folder data/input dan data/output bisa diakses.",
        )
    except LLMGenerationError as exc:
        print_error(
            title="LLM Error",
            detail=exc.message,
            hint="Pastikan Ollama berjalan dan model tersedia.",
        )
    except AgentDirectorError as exc:
        print_error(title="Agent Director Error", detail=exc.message)
    except KeyboardInterrupt:
        console.print()
        console.print("[warning]  Interrupted oleh user.[/warning]")
