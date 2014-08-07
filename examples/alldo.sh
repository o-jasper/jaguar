#!/bin/bash

# How to do bash in makefiles -_- ... both make and bash sucks, probably.

while read line; do $1 $line$2; done
