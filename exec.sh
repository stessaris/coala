#!/bin/bash
export PYTHONPATH=$PYTHONPATH:"$(dirname "$0")"
python "$(dirname "$0")"/coala/coala "$@"