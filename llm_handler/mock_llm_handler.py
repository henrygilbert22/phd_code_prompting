import os
from typing import List, Optional, ClassVar, Protocol
import enum

import utils.llm_handler_interface as llm_handler_interface


class MockLLMHandler(llm_handler_interface.LLMHandler):

    _text_completion: Optional[List[str]]
    _chat_completion: Optional[List[str]]
    _text_embedding: Optional[List[float]]

    def __init__(self,
                 text_completion: Optional[List[str]] = None,
                 chat_completion: Optional[List[str]] = None,
                 text_embedding: Optional[List[float]] = None):
        self._text_completion = text_completion
        self._chat_completion = chat_completion
        self._text_embedding = text_embedding

    def get_text_completion(self,
                            prompt: str,
                            model: Optional[enum.Enum] = None,
                            max_tokens: int = 1000,
                            samples: int = 1,
                            **kwargs) -> List[str]:
        if not self._text_completion:
            raise ValueError(f'_text_completion not set')
        return self._text_completion

    def get_chat_completion(self,
                            messages: List,
                            model: Optional[enum.Enum] = None,
                            samples: int = 1,
                            **kwargs) -> List[str]:
        if not self._chat_completion:
            raise ValueError(f'_chat_completion not set')
        return self._chat_completion

    def get_text_embedding(
        self,
        input: str,
        model: Optional[enum.Enum] = None,
    ) -> List[float]:
        if not self._text_embedding:
            raise ValueError(f'_text_embedding not set')
        return self._text_embedding
