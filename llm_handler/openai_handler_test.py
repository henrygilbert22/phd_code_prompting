import os
from typing import  List
from unittest import mock
import pytest
import openai

import openai_handler as openai_handler


@pytest.fixture(autouse=True)
def local_env_setup():
    if not os.path.exists('.env.secret'):
        return
    with open('.env.secret', 'r') as env_file:
        for line in env_file.readlines():
            key, value = line.split('=')
            os.environ[key] = value


# Clear openai.api_key before each test
@pytest.fixture(autouse=True)
def test_env_setup():
    openai.api_key = os.environ.get(openai_handler.OpenAIHandler._ENV_KEY_NAME)


# This allows us to clear the OPENAI_API_KEY before any test we want
@pytest.fixture()
def mock_settings_env_vars():
    with mock.patch.dict(os.environ, clear=True):
        yield


# Define some constants for our tests
_TEST_MESSAGE: str = "Hello how are you?"
_TEXT_EMBEDDING_ADA_002_LENGTH = 1536
def test_get_text_embedding():
    # Ensure we are using text-embedding-ada-002 for this test
    handler = openai_handler.OpenAIHandler()
    model = openai_handler.EmbeddingModelVersion()
    assert model.ADA_002.value == 'text-embedding-ada-002'
    # Ensure we get the desired number of chat_completions
    embedding = handler.get_text_embedding(input=_TEST_MESSAGE, model=model)
    assert isinstance(embedding, List)
    assert len(embedding) == _TEXT_EMBEDDING_ADA_002_LENGTH
    for value in embedding:
        assert isinstance(value, float)
        assert not value == 0
