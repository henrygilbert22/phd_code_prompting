#!/usr/bin/env bash

set -e
cd "$(dirname "$0")"/../..
. setup/lib/SYSTEM.sh

declare -r PYTHON_EXEC="${PYTHON_EXEC:-$PYENV_BIN/python3}"
echo "BIN_PATH: ${BIN_PATH} python: $PYTHON_EXEC"
mkdir -p "${BIN_PATH}"

for proto in $(find . -name '*.proto'); do

    # check if proot is a service
    if grep -q "service" $proto; then
        echo "Service: $proto"
        # remove .proto from file name and ./ from proto file start
        api_path=${proto%.proto}
        api_path=${api_path#./}
        api_path="${BIN_PATH}/${api_path}_api.pb"
        echo "Compiling $proto to $api_path"
        $PYTHON_EXEC -m grpc_tools.protoc --proto_path=. --python_out="${BIN_PATH}" --pyi_out="${BIN_PATH}"  --grpc_python_out="${BIN_PATH}" --descriptor_set_out="${BIN_PATH}" --include_imports $proto
        continue
    fi
    echo "Compiling $proto"
    $PYTHON_EXEC -m grpc_tools.protoc --proto_path=. --python_out="${BIN_PATH}" --pyi_out="${BIN_PATH}"  $proto
done
