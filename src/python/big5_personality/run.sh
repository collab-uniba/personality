#!/bin/bash
export PYTHONPATH=$PYTHONPATH:../:../apache_projects
# mandatory param: tool name, either liwc or p_insights
# optional param: reset, to empty the db tables containing personality data
python big5.py $@
