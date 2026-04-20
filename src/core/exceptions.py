from __future__ import annotations


class AgentDirectorError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class StorageError(AgentDirectorError):
    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"Storage error at '{path}': {reason}")


class LLMGenerationError(AgentDirectorError):
    def __init__(self, model: str, reason: str) -> None:
        self.model = model
        self.reason = reason
        super().__init__(f"LLM generation failed (model='{model}'): {reason}")
