#!/bin/bash

set -e
cd "$(dirname "$0")/../.."
. setup/lib/SYSTEM.sh

setup_osx() {
    brew install pyenv
    brew install pyenv-virtualenv
}

setup_ubuntu() {
    sudo apt-get update
    sudo apt install -y make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python3-openssl git
    curl https://pyenv.run | bash
}

config_shell() {
    declare -r SHELL_PATH=$1
    echo "export PYENV_ROOT=\"$PYENV_ROOT\"" >> "$SHELL_SCRIPT"
    echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> "$SHELL_SCRIPT"
    echo 'eval "$(pyenv init -)"' >> "$SHELL_SCRIPT"
    echo 'eval "$(pyenv virtualenv-init -)"' >> "$SHELL_SCRIPT"
    source "$SHELL_SCRIPT"
}

echo "Idenitified OS: $OSTYPE"
if command -v pyenv 1>/dev/null 2>&1; then
    echo "Pyenv already setup in Shell"
    exit 0
fi

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Running Ubuntu Pyenv Setup"    
    setup_ubuntu
    declare SHELL_SCRIPT=$HOME/.bashrc
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Running Mac Pyenv Setup"
    setup_osx
    declare SHELL_SCRIPT=$HOME/.zshrc
else
    echo "OS not supported"
    exit 1
fi

echo "Setting up Pyenv in Shell with $SHELL_SCRIPT as shell script and $PATH as path"
config_shell "$SHELL_SCRIPT"  


