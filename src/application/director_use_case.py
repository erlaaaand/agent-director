from __future__ import annotations

import logging
from datetime import datetime, timezone

from src.core.entities import CreativeDocumentBatch, ScriptDocumentBatch
from src.core.exceptions import LLMGenerationError, StorageError
from src.core.ports import LLMPort, StoragePort

logger = logging.getLogger(__name__)


class DirectorUseCase:
    def __init__(self, storage: StoragePort, llm: LLMPort) -> None:
        self._storage = storage
        self._llm = llm

    def execute(self, target_filename: str | None = None) -> list[ScriptDocumentBatch]:
        if target_filename is not None:
            files = [target_filename]
        else:
            files = self._storage.list_input_files()

        if not files:
            logger.info("Tidak ada file input yang ditemukan.")
            return []

        logger.info("Memproses %d file.", len(files))
        results: list[ScriptDocumentBatch] = []

        for filename in files:
            try:
                batch = self._process_file(filename)
                results.append(batch)
            except StorageError as exc:
                logger.error("Storage error pada file '%s': %s", filename, exc.message)
            except Exception as exc:
                logger.error("Error tidak terduga pada file '%s': %s", filename, exc)

        return results

    def get_file_preview(self, filename: str) -> CreativeDocumentBatch:
        return self._storage.read_input(filename)

    def _process_file(self, filename: str) -> ScriptDocumentBatch:
        logger.info("Memproses file: '%s'", filename)
        input_batch = self._storage.read_input(filename)

        scripts = []
        for doc in input_batch.documents:
            try:
                script = self._llm.generate_script(doc)
                scripts.append(script)
                logger.info(
                    "Skrip berhasil dibuat  topic='%s'  id='%s'",
                    doc.trend_identity.topic,
                    doc.document_id,
                )
            except LLMGenerationError as exc:
                logger.error(
                    "Gagal generate skrip untuk topic='%s': %s",
                    doc.trend_identity.topic,
                    exc.message,
                )

        output_batch = ScriptDocumentBatch(
            region=input_batch.region,
            date=input_batch.date,
            scripts=scripts,
        )

        ts = datetime.now(tz=timezone.utc).strftime("%H%M%SZ")
        output_filename = f"scripts_{input_batch.region}_{input_batch.date}_{ts}.json"
        self._storage.save_output(output_batch, output_filename)
        self._storage.archive_input(filename)

        logger.info(
            "File '%s' selesai  scripts=%d  output='%s'",
            filename,
            len(scripts),
            output_filename,
        )
        return output_batch