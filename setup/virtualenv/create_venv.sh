#!/bin/bash

echo "Setting up virtualenv with dirname $0"
cd "$(dirname "$0")"/../..
echo "Working directory is $(pwd)"

. setup/lib/SYSTEM.sh    

echo "Installing ${VIRTUAL_ENV_VERSION} if it doesn't exist"
pyenv install $VIRTUAL_ENV_VERSION -s

# check if code_prompting virtualenv exists, otherwise create it
if pyenv virtualenvs | grep -q $VIRTUAL_ENV_NAME; then
    echo "${VIRTUAL_ENV_NAME} virtualenv already exists"
else
    echo "Creating ${VIRTUAL_ENV_NAME} virtualenv"
    pyenv virtualenv $VIRTUAL_ENV_VERSION $VIRTUAL_ENV_NAME
    VENV_ACTIVATE="$PYENV_ROOT/versions/$VIRTUAL_ENV_NAME/bin/activate"
    PYTHONPATH="$REPO_PATH:$REPO_PATH/.bin"
    echo "Setting env vars in $VENV_ACTIVATE"
    echo "export PYTHONPATH=\"$PYTHONPATH\"" >> $VENV_ACTIVATE
    echo "export PATH=\"$PYENV_PATH\"" >> $VENV_ACTIVATE
    echo "echo 'Activated ${PYTHONPATH} virtualenv'" >> $VENV_ACTIVATE
fi

echo "Setting ${VIRTUAL_ENV_NAME} as local python"
pyenv local $VIRTUAL_ENV_NAME
