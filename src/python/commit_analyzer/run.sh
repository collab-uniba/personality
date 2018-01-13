#!/bin/bash
export PYTHONPATH=$PYTHONPATH:../:../apache_projects
python parse_commits.py ../git_cloner/apache_repos
