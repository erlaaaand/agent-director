from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.core.entities import CreativeDocumentBatch, ScriptDocumentBatch
from src.core.exceptions import StorageError
from src.core.ports import StoragePort

logger = logging.getLogger(__name__)


class _DateTimeEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class LocalStorageAdapter(StoragePort):
    def __init__(self, input_path: str, output_path: str) -> None:
        self._input = Path(input_path).resolve()
        self._output = Path(output_path).resolve()
        self._archive = self._input / "_processed"
        for d in [self._input, self._output, self._archive]:
            try:
                d.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                raise StorageError(path=str(d), reason=str(exc)) from exc

    def list_input_files(self) -> list[str]:
        return sorted(
            p.name for p in self._input.glob("*.json")
            if p.is_file() and not p.name.startswith("_")
        )

    def read_input(self, filename: str) -> CreativeDocumentBatch:
        path = self._input / filename
        try:
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
            return CreativeDocumentBatch.model_validate(data)
        except FileNotFoundError:
            raise StorageError(path=str(path), reason="File tidak ditemukan.") from None
        except (json.JSONDecodeError, Exception) as exc:
            raise StorageError(path=str(path), reason=str(exc)) from exc

    def save_output(self, batch: ScriptDocumentBatch, filename: str) -> None:
        target = self._output / filename
        tmp = target.with_suffix(".tmp")
        try:
            payload = json.dumps(
                batch.model_dump(mode="json"),
                indent=2,
                ensure_ascii=False,
                cls=_DateTimeEncoder,
            )
            tmp.write_text(payload, encoding="utf-8")
            tmp.replace(target)
            logger.info("Output disimpan → %s", target)
        except (OSError, TypeError, ValueError) as exc:
            tmp.unlink(missing_ok=True)
            raise StorageError(path=str(target), reason=str(exc)) from exc

    def archive_input(self, filename: str) -> None:
        src = self._input / filename
        dst = self._archive / filename
        try:
            shutil.move(str(src), str(dst))
            logger.info("Input diarsipkan: '%s' → _processed/", filename)
        except (OSError, shutil.Error) as exc:
            logger.warning("Gagal mengarsipkan '%s': %s", filename, exc)
