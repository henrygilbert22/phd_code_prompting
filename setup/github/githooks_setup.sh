#!/usr/bin/env bash

set -e
cd "$(dirname "$0")"/../..
echo "Setting up git hooks in $(pwd)"

# Create a symlink to the pre-commit hook
for hook in setup/github/githooks/*; do
    echo "Setting up $hook"
    ln -sf "../../$hook" .git/hooks/$(basename "$hook")
done
