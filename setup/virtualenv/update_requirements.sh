#!/bin/bash

set -e
cd "$(dirname "$0")/../.."

. setup/lib/SYSTEM.sh


echo "Installing requirements with: $PYENV_BIN"
$PYENV_BIN/pip install --upgrade pip
$PYENV_BIN/pip install -r "$SETUP_PATH/virtualenv/requirements.txt"


