#!/bin/bash

CONDAROOT=~/miniconda3

CONDAENV=analysis

source $CONDAROOT/etc/profile.d/conda.sh

conda activate "$CONDAENV"

cd "$(dirname "$0")/../.."

bash
