#!/bin/bash
export PYTHONPATH=$PYTHONPATH:../
mkdir -p ./apache_repos
python clone_projects.py
