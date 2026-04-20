from __future__ import annotations

import logging
import sys

from rich.logging import RichHandler

from config import get_settings
from src.application.director_use_case import DirectorUseCase
from src.infrastructure.llm.ollama_adapter import OllamaLLMAdapter
from src.infrastructure.local_storage import LocalStorageAdapter
from src.interfaces.cli import run_cli


def _configure_logging(level: str) -> None:
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                rich_tracebacks=False,
                markup=True,
                show_path=False,
                omit_repeated_times=False,
            )
        ],
        force=True,
    )


def main() -> None:
    settings = get_settings()
    _configure_logging(settings.LOG_LEVEL)
    logger = logging.getLogger(__name__)

    logger.info(
        "agent_director starting  "
        "model=[magenta]'%s'[/magenta]  "
        "input=[cyan]'%s'[/cyan]  "
        "output=[green]'%s'[/green]",
        settings.OLLAMA_MODEL,
        settings.INPUT_DATA_PATH,
        settings.OUTPUT_DATA_PATH,
    )

    storage = LocalStorageAdapter(
        input_path=settings.INPUT_DATA_PATH,
        output_path=settings.OUTPUT_DATA_PATH,
    )

    llm = OllamaLLMAdapter(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        timeout=settings.OLLAMA_TIMEOUT,
        retries=settings.OLLAMA_RETRIES,
    )

    use_case = DirectorUseCase(storage=storage, llm=llm)

    run_cli(use_case=use_case)


if __name__ == "__main__":
    main()
