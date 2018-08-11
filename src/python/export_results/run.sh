#!/usr/bin/env bash
export PYTHONPATH=$PYTHONPATH:../:../apache_projects:../history_analyzer
# mandatory param: tool name, either liwc or p_insights
python export.py $@