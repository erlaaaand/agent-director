from __future__ import annotations

import json
import logging
from typing import Any, Final

import httpx

from src.core.entities import CreativeDocument, ScriptDocument
from src.core.exceptions import LLMGenerationError
from src.core.ports import LLMPort
from src.infrastructure.llm.parser import parse_script_document
from src.infrastructure.llm.prompts import SYSTEM_PROMPT, EDITOR_SYSTEM_PROMPT, build_user_message, build_editor_message

logger = logging.getLogger(__name__)

_CHAT_PATH: Final[str] = "/api/chat"


class OllamaLLMAdapter(LLMPort):
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:7b",
        timeout: float = 180.0,
        retries: int = 2,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._retries = retries
        self._url = f"{self._base_url}{_CHAT_PATH}"

    def generate_script(self, document: CreativeDocument) -> ScriptDocument:
        user_msg = build_user_message(document)
        fallback_duration = document.creative_brief.video_parameters.target_duration_seconds
        last_exc: Exception | None = None

        for attempt in range(1, self._retries + 1):
            logger.info(
                "Ollama call  model='%s'  topic='%s'  attempt=%d/%d",
                self._model,
                document.trend_identity.topic,
                attempt,
                self._retries,
            )
            try:
                raw = self._call_ollama(user_msg)
                return parse_script_document(
                    content=raw,
                    model=self._model,
                    document_id=document.document_id,
                    topic=document.trend_identity.topic,
                    fallback_duration=fallback_duration,
                )
            except LLMGenerationError:
                raise
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "Attempt %d/%d gagal (%s: %s). %s",
                    attempt,
                    self._retries,
                    type(exc).__name__,
                    exc,
                    "Mencoba lagi..." if attempt < self._retries else "Menyerah.",
                )

        raise LLMGenerationError(
            model=self._model,
            reason=f"Semua {self._retries} percobaan gagal. Error terakhir: {last_exc}",
        )

    def _call_ollama(self, user_message: str) -> str:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "stream": True,
            "format": "json",
            "options": {
                "temperature": 0.4,
                "num_predict": 2048,
                "repeat_penalty": 1.15,
                "num_ctx": 4096,
            },
        }

        try:
            tokens: list[str] = []
            with httpx.Client(
                timeout=httpx.Timeout(
                    connect=15.0,
                    read=self._timeout,
                    write=15.0,
                    pool=5.0,
                )
            ) as client:
                with client.stream("POST", self._url, json=payload) as resp:
                    if resp.status_code >= 400:
                        body = resp.read().decode("utf-8", errors="replace")
                        raise LLMGenerationError(
                            model=self._model,
                            reason=f"Ollama HTTP {resp.status_code}: {body[:300]}",
                        )
                    for line in resp.iter_lines():
                        if not line.strip():
                            continue
                        try:
                            chunk: dict[str, Any] = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        token = (
                            chunk.get("message", {}).get("content", "")
                            or chunk.get("response", "")
                        )
                        if token:
                            tokens.append(token)
                        if chunk.get("done"):
                            break

        except LLMGenerationError:
            raise
        except httpx.ConnectError:
            raise LLMGenerationError(
                model=self._model,
                reason=(
                    f"Tidak bisa konek ke Ollama di '{self._base_url}'. "
                    "Pastikan Ollama berjalan."
                ),
            ) from None
        except httpx.TimeoutException:
            raise LLMGenerationError(
                model=self._model,
                reason=f"Ollama timeout setelah {self._timeout}s.",
            ) from None
        except httpx.HTTPError:
            raise LLMGenerationError(
                model=self._model,
                reason="HTTP error ke Ollama.",
            ) from None

        content = "".join(tokens)
        if not content:
            raise LLMGenerationError(
                model=self._model,
                reason="Ollama mengembalikan response kosong.",
            )
        return content
