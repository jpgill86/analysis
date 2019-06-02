#!/bin/bash

CONDAENV=analysis

CONDAROOT=$(dirname $(which conda))/..

source $CONDAROOT/etc/profile.d/conda.sh

conda activate "$CONDAENV"

cd ..
python "launch-data-explorer.py"
