from __future__ import annotations

import logging
import sys

from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from src.application.director_use_case import DirectorUseCase
from src.core.exceptions import AgentDirectorError, LLMGenerationError, StorageError
from src.interfaces.cli_components.display import (
    print_error,
    print_file_preview,
    print_goodbye,
    print_header,
    print_no_files,
    print_results,
)
from src.interfaces.cli_components.prompts import prompt_file_action, prompt_main_menu
from src.interfaces.cli_components.theme import console

logger = logging.getLogger(__name__)


def _run_generate(use_case: DirectorUseCase, target: str | None) -> None:
    label = f"[bold]{target}[/bold]" if target else "semua file"
    try:
        with Progress(
            SpinnerColumn(spinner_name="dots", style="cyan"),
            TextColumn(f"[white]Generating scripts untuk {label}…[/white]"),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("", total=None)
            batches = use_case.execute(target_filename=target)
            progress.stop_task(task)
        print_results(batches)
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


def _run_preview(use_case: DirectorUseCase, filename: str) -> None:
    try:
        batch = use_case.get_file_preview(filename)
        print_file_preview(batch, filename)
    except StorageError as exc:
        print_error(
            title="Preview Gagal",
            detail=exc.message,
            hint="Periksa apakah file JSON valid dan bisa dibaca.",
        )


def run_cli(use_case: DirectorUseCase) -> None:
    print_header()

    while True:
        try:
            files = use_case._storage.list_input_files()
        except Exception as exc:
            print_error(title="Error Scan Folder", detail=str(exc))
            sys.exit(1)

        if not files:
            print_no_files()
            try:
                raw = console.input(
                    "[prompt]  Tekan Enter untuk scan ulang, atau ketik E untuk exit: [/prompt]"
                ).strip().lower()
            except (KeyboardInterrupt, EOFError):
                console.print()
                print_goodbye()
                sys.exit(0)
            if raw == "e":
                print_goodbye()
                sys.exit(0)
            continue

        try:
            action, selected_file = prompt_main_menu(files)
        except (KeyboardInterrupt, EOFError):
            console.print()
            print_goodbye()
            sys.exit(0)

        if action == "exit":
            print_goodbye()
            sys.exit(0)

        if action == "all":
            _run_generate(use_case, target=None)
            continue

        if action == "file" and selected_file is not None:
            while True:
                try:
                    file_action = prompt_file_action(selected_file)
                except (KeyboardInterrupt, EOFError):
                    console.print()
                    break

                if file_action == "back":
                    break

                if file_action == "preview":
                    _run_preview(use_case, selected_file)
                    continue

                if file_action == "generate":
                    _run_generate(use_case, target=selected_file)
                    break