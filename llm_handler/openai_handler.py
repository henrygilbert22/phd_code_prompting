from __future__ import annotations
import openai
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion import ChatCompletion
import os
from typing import List, Optional, ClassVar, Dict, Union, cast
import backoff
import enum
import numpy as np

import llm_handler.llm_handler_interface as llm_handler_interface
import proto.patched_solutions_pb2 as ps_pb2


class ChatModelVersion(enum.Enum,
                       metaclass=llm_handler_interface.DefaultEnumMeta):
    GPT_3_5_TURBO = 'gpt-3.5-turbo-1106'
    GPT_4 = 'gpt-4'
    GPT_4_TURBO = 'gpt-4-0125-preview'


class EmbeddingModelVersion(enum.Enum,
                            metaclass=llm_handler_interface.DefaultEnumMeta):
    ADA_002 = 'text-embedding-ada-002'


class OpenAIHandler(llm_handler_interface.LLMHandler):

    _MODEL_NAME_TO_VERSION: ClassVar[Dict['ps_pb2.ModelType', str]] = {
        ps_pb2.MODEL_TYPE_GPT_3_5_TURBO: 'gpt-3.5-turbo-0125',
        ps_pb2.MODEL_TYPE_GPT_4_TURBO: 'gpt-4-turbo-preview'
    }

    _ENV_KEY_NAME: ClassVar[str] = 'OPENAI_API_KEY'

    @classmethod
    def _read_key_from_file(cls, file_path: str) -> str:
        with open(file_path, "r") as f:
            for line in f:
                key, value = line.strip().split("=")
                if 'OPENAI_API_KEY' in key:
                    return value
        raise ValueError(f'No OPENAI_API_KEY in {file_path}')

    def __init__(self, file_path: Optional[str] = None):
        openai_api_key = os.environ.get(self._ENV_KEY_NAME)
        if file_path:
            openai_api_key = self._read_key_from_file(file_path)
        if not openai_api_key:
            raise ValueError(f'{self._ENV_KEY_NAME} not found')
        openai.api_key = openai_api_key

    @classmethod
    def get_model_version(cls, model_type: 'ps_pb2.ModelType') -> str:
        if model_type not in cls._MODEL_NAME_TO_VERSION:
            raise ValueError(f'Invalid model: {model_type}')
        return cls._MODEL_NAME_TO_VERSION[model_type]

    def get_text_completion(self, prompt: str, model: enum.Enum,
                            max_tokens: int, samples: int,
                            **kwargs) -> List[str]:
        ...

    @backoff.on_exception(backoff.expo, openai.RateLimitError)
    def get_chat_completion(self,
                            messages: Union[List[ChatCompletionMessageParam],
                                            List[Dict[str, str]]],
                            model_type: 'ps_pb2.ModelType', **kwargs) -> str:
        model = self.get_model_version(model_type)
        response: ChatCompletion = openai.chat.completions.create(
            model=model,
            messages=cast(List[ChatCompletionMessageParam], messages),
            n=1,
            **kwargs)
        if len(response.choices) != 1:
            raise ValueError(f'Expected one choice in response: {response}')
        if response.choices[0].finish_reason != 'stop' or not response.choices[
                0].message.content:
            raise ValueError(
                f'Choice did not complete correctly: {response.choices[0]}')
        return response.choices[0].message.content

    @backoff.on_exception(backoff.constant,
                          openai.RateLimitError,
                          interval=30,
                          jitter=None)
    def get_text_embedding(
            self,
            input: str,
            model: Optional[EmbeddingModelVersion] = None) -> List[float]:
        MODEL_DEFAULT: EmbeddingModelVersion = EmbeddingModelVersion()
        model = model or MODEL_DEFAULT
        response = openai.embeddings.create(model=model.value,
                                            encoding_format='float',
                                            input=input)
        if not response.data:
            raise ValueError(f'No embedding in response: {response}')
        elif len(response.data) != 1:
            raise ValueError(
                f'More than one embedding in response: {response}')
        return np.array(response.data[0].embedding, dtype=float).tolist()
