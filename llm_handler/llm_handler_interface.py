from __future__ import annotations
from typing import List, Optional, ClassVar, Protocol
import enum


class DefaultEnumMeta(enum.EnumMeta):

    def __call__(cls, value=None, *args, **kwargs) -> DefaultEnumMeta:
        if value is None:
            return next(iter(cls))
        return super().__call__(value, *args, **kwargs)  # type: ignore


class LLMHandler(Protocol):

    def get_text_completion(self, prompt: str, model: enum.Enum,
                            max_tokens: int, samples: int,
                            **kwargs) -> List[str]:
        ...

    def get_chat_completion(self, messages: List, model: enum.Enum,
                            samples: int, **kwargs) -> List[str]:
        ...

    def get_text_embedding(self, input: str, model: enum.Enum) -> List[float]:
        ...
