from __future__ import annotations
import openai
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
import os
from typing import List, Optional, ClassVar, Literal
import backoff
import enum
import numpy as np

import utils.llm_handler_interface as llm_handler_interface


class ChatModelVersion(enum.Enum, metaclass=llm_handler_interface.DefaultEnumMeta):
    GPT_3_5 = 'gpt-3.5-turbo-1106'
    GPT_4 = 'gpt-4'
    GPT_4_TURBO = 'gpt-4-1106-preview'


class EmbeddingModelVersion(enum.Enum, metaclass=llm_handler_interface.DefaultEnumMeta):
    ADA_002 = 'text-embedding-ada-002'


class OpenAIHandler(llm_handler_interface.LLMHandler):

    _ENV_KEY_NAME: ClassVar[str] = 'OPENAI_API_KEY'

    def __init__(self, openai_api_key: Optional[str] = None):
        _openai_api_key = openai_api_key or os.environ.get(self._ENV_KEY_NAME)
        if not _openai_api_key:
            raise ValueError(f'{self._ENV_KEY_NAME} not set')
        openai.api_key = _openai_api_key

    @backoff.on_exception(backoff.expo, openai.RateLimitError)
    def get_text_completion(self,
                            prompt: str,
                            model: Optional[EmbeddingModelVersion] = None,
                            max_tokens: int = 1000,
                            samples: int = 1,
                            **kwargs) -> List[str]:
        MODEL_DEFAULT: EmbeddingModelVersion = EmbeddingModelVersion()
        model = model or MODEL_DEFAULT
        response: openai.types.Completion = openai.completions.create(model=model.value,
                                                                      prompt=prompt,
                                                                      max_tokens=max_tokens,
                                                                      n=samples,
                                                                      **kwargs)
        return [choice.text for choice in response.choices]

    @backoff.on_exception(backoff.expo, openai.RateLimitError)
    def get_chat_completion(self,
                            messages: List[ChatCompletionMessageParam],
                            model: Optional[ChatModelVersion] = None,
                            samples: int = 1,
                            **kwargs) -> List[str]:
        MODEL_DEFAULT: ChatModelVersion = ChatModelVersion()
        model = model or MODEL_DEFAULT
        response = openai.chat.completions.create(model=model.value,
                                                  messages=messages,
                                                  n=samples,
                                                  **kwargs)
        responses: List[str] = []
        for choice in response.choices:
            if choice.finish_reason != 'stop' or not choice.message.content:
                raise ValueError(f'Choice did not complete correctly: {choice}')
            responses.append(choice.message.content)
        return responses

    @backoff.on_exception(backoff.constant, openai.RateLimitError, interval=30, jitter=None)
    def get_text_embedding(self,
                           input: str,
                           model: Optional[EmbeddingModelVersion] = None) -> List[float]:
        MODEL_DEFAULT: EmbeddingModelVersion = EmbeddingModelVersion()
        model = model or MODEL_DEFAULT
        response = openai.embeddings.create(model=model.value, encoding_format='float', input=input)
        if not response.data:
            raise ValueError(f'No embedding in response: {response}')
        elif len(response.data) != 1:
            raise ValueError(f'More than one embedding in response: {response}')
        return np.array(response.data[0].embedding, dtype=float).tolist()
