#!/bin/bash
export PYTHONPATH=$PYTHONPATH:../:../apache_projects
python pr_extractor.py ../git_cloner/apache_repos
