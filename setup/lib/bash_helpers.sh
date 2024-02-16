#!bin/bash

# Colors for user friendliness
declare -r GREEN='\033[0;32m'
declare -r BLUE='\033[1;34m'
declare -r RED='\033[0;31m'
declare -r GREY='\033[0;37m'
declare -r NC='\033[0m' # No Color

# Define helper functions
headline() {
  echo -e "--- ${BLUE}$*${NC} ---"
}

error-message() {
    echo -e "--- ${RED}ERROR: $*${NC} ---"
}

success () {
    if [ "$#" -eq 0 ]; then
        echo -e "--- ${GREEN}Success${NC} ---\n"
    else
        echo -e "--- ${GREEN}Success: $*${NC} ---"
    fi
}