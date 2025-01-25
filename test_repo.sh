#!/bin/bash

REPO_PATH="$1"
COMMIT_HASH="$2"

source run_or_fail.sh
rm -f .commit_id

run_or_fail "Repository folder not found" pushd "$REPO_PATH" 1> /dev/null
run_or_fail "Could not clean repository" git clean -d -f -x
run_or_fail "Could not call git pull" git pull
run_or_fail "Could not update to given commit hash" git reset --hard "$COMMIT_HASH"
run_or_fail "Repository folder not found" pushd "$REPO_PATH/tests" 1> /dev/null
TEST_OUTPUT=$(python -m unittest discover -s . 2>&1)
popd 1> /dev/null
popd 1> /dev/null
echo "$TEST_OUTPUT" > "results"