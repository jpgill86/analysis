#!/bin/bash

echo "Starting"

CONDAENV=analysis

CONDAROOT=$(dirname $(which conda))/..

source $CONDAROOT/etc/profile.d/conda.sh

conda activate "$CONDAENV"

neurotic
