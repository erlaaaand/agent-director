from __future__ import annotations

from abc import ABC, abstractmethod

from src.core.entities import CreativeDocument, CreativeDocumentBatch, ScriptDocument, ScriptDocumentBatch


class StoragePort(ABC):
    @abstractmethod
    def list_input_files(self) -> list[str]:
        ...

    @abstractmethod
    def read_input(self, filename: str) -> CreativeDocumentBatch:
        ...

    @abstractmethod
    def save_output(self, batch: ScriptDocumentBatch, filename: str) -> None:
        ...

    @abstractmethod
    def archive_input(self, filename: str) -> None:
        ...


class LLMPort(ABC):
    @abstractmethod
    def generate_script(self, document: CreativeDocument) -> ScriptDocument:
        ...

    @abstractmethod
    def refine_script(self, draft: ScriptDocument) -> ScriptDocument:
        ...