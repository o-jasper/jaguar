#!/bin/bash

# Argument is the name of the test, stdin is the output of the test.
#
# * Run program output temporary.
# * If different that previous:
#   + Mention
#   + store output of current commit.
# * if BUG occurs, mention.

RESULT=/tmp/runtest.$(date +%s)$RANDOM
cat > $RESULT

grep BUG $RESULT  # Print all bugs in there.

mkdir -p .result/$1/last/

if [ -e .result/$1/last/* ]; then
    if [ "$(diff -q .result/$1/last/* $RESULT)" == "" ]; then
        # Exists and matches, its good.
        exit
    fi
fi

echo .result/$1/last/* DIFFERS
mv .result/$1/last/* .result/$1/  # No longer last.

get_commit()
{
    git log --skip "$1" -n 1 |head -n 1 |cut -f 2 -d' '
}

# Current is last.
mv $RESULT .result/$1/last/$(get_commit)
