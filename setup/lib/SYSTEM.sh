#!/bin/bash

declare -r VIRTUAL_ENV_NAME="${VIRTUAL_ENV_NAME:-code_prompting}"
declare -r VIRTUAL_ENV_VERSION="${VIRTUAL_ENV_VERSION:-3.10.12}"

SCRIPT_PATH=$(dirname "$0")
declare -r REPO_PATH=$(cd "$SCRIPT_PATH/../.." && pwd)
declare -r SETUP_PATH="${REPO_PATH}/setup"
declare -r BIN_PATH="${BIN_PATH:-$REPO_PATH/.bin}"
declare -r PYENV_ROOT="$HOME/.pyenv"
declare -r PYENV_BIN="$HOME/.pyenv/versions/$VIRTUAL_ENV_NAME/bin"
declare -r PYENV_PATH="$PYENV_ROOT/bin:$PATH"

declare -rx PATH="$PYENV_ROOT/bin:$PATH"
