#!/bin/bash

set -e

# go to dir of this script 
cd $(dirname "$0")/../../

echo "Installing pyenv"
setup/virtualenv/install_pyenv.sh

echo "Creating virtualenv"
setup/virtualenv/create_venv.sh

echo "Activating virtualenv"
setup/virtualenv/install_requirements.sh

echo "If you want to use this virtualenv in your current shell, reactivate it"
