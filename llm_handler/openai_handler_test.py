import os
from typing import ClassVar, List
from unittest import mock
import logging
import pytest
import openai
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam

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
    openai.api_key = None
    env_file = open('.env.secret', 'r')
    env_lines = env_file.readlines()
    env_file.close()
    for line in env_lines:
        key, value = line.split('=')
        os.environ[key] = value
    

# This allows us to clear the OPENAI_API_KEY before any test we want
@pytest.fixture()
def mock_settings_env_vars():
    with mock.patch.dict(os.environ, clear=True):
        yield


# Define some constants for our tests
_TEST_KEY: str = "TEST_KEY"
_TEST_MESSAGE: str = "Hello how are you?"
_TEST_MESSAGE_FOR_CHAT_COMPLETION: List[ChatCompletionMessageParam] = [{
    "role":
    "system",
    "content":
    "You are serving as a en endpoint to verify a test."
}, {
    "role":
    "user",
    "content":
    "Respond with something to help us verify our code is working."
}]
_TEXT_EMBEDDING_ADA_002_LENGTH = 1536


def test_init_without_key(mock_settings_env_vars):
    # Ensure key not set as env var and openai.api_key not set
    with pytest.raises(KeyError):
        os.environ[openai_handler.OpenAIHandler._ENV_KEY_NAME]
    assert openai.api_key == None
    # Ensure proper exception raised when instantiating handler without key as param or env var
    with pytest.raises(ValueError) as excinfo:
        openai_handler.OpenAIHandler()
    assert f'{openai_handler.OpenAIHandler._ENV_KEY_NAME} not set' in str(
        excinfo.value)
    assert openai.api_key == None


def test_init_with_key_as_param():
    # Ensure key is set as env var, key value is unique from _TEST_KEY, and openai.api_key not set
    assert not os.environ[
        openai_handler.OpenAIHandler._ENV_KEY_NAME] == _TEST_KEY
    assert openai.api_key == None
    # Ensure successful instantiation and openai.api_key properly set
    handler = openai_handler.OpenAIHandler(openai_api_key=_TEST_KEY)
    assert isinstance(handler, openai_handler.OpenAIHandler)
    assert openai.api_key == _TEST_KEY


def test_init_with_key_as_env_var(mock_settings_env_vars):
    # Ensure key not set as env var and openai.api_key not set
    with pytest.raises(KeyError):
        os.environ[openai_handler.OpenAIHandler._ENV_KEY_NAME]
    assert openai.api_key == None
    # Set key as env var
    os.environ.setdefault(openai_handler.OpenAIHandler._ENV_KEY_NAME,
                          _TEST_KEY)
    # Ensure successful instantiation and openai.api_key properly set
    handler = openai_handler.OpenAIHandler()
    assert isinstance(handler, openai_handler.OpenAIHandler)
    assert openai.api_key == _TEST_KEY


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
