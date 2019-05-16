#!/bin/bash

CONDAROOT=~/miniconda3

CONDAENV=analysis

source $CONDAROOT/etc/profile.d/conda.sh

conda activate "$CONDAENV"

jupyter notebook "$(dirname "$0")/../../notebooks"
