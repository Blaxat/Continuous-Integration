#!/bin/bash

run_or_fail() {
    local error_message="$1"
    shift
    "$@"
    local status=$?

    if [ $status -ne 0 ]; then
        echo "$error_message" >&2
        exit $status
    fi
}

