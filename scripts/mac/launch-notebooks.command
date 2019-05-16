#!/bin/bash

CONDAENV=analysis

CONDAROOT=$(dirname $(which conda))/..

source $CONDAROOT/etc/profile.d/conda.sh

conda activate "$CONDAENV"

jupyter notebook "$(dirname "$0")/../../notebooks"
