#!/usr/bin/env bash

cd $(dirname "$0")/..

echo "Setting up Pyenv and Virtualenv"
setup/virtualenv/setup.sh

echo "Compiling Protobufs"
setup/protobuf/compile_protos.sh

echo "Setting up Git Hooks"
setup/github/githooks_setup.sh

