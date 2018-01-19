# personality

## 1. Cloning
```bash
$ git clone https://github.com/collab-uniba/personality.git --recursive
```

## 2. Crawl Apache projects

*Setup*

Use Python 3 environment and install packages from `src/python/requirements.txt`

*Execution*

From directory `src/python/apache_crawler` run:
```bash
$ scrapy apache_crawler -t (json|csv) -o apache-projects.(json|csv) [-L DEBUG --logfile apache.log]
```

## 3. Mine mailing lists (for git projects only)

*Setup*

Use Python 2 environment and install packages from `src/python/ml_downloader/requirements.txt`.
Create database schema importing the file `submodules/mlminer/db/data_model_mysql.sql`.
```bash
$ mysql -u <user> -p<password> < data_model_mysql.sql
```

*Execution*

From directory `src/python/ml_downloader` run:
```bash
$ sh run.sh
```

## 4. Clone git projects

*Setup*

USe Python 3 environment as described in Step 2.

*Execution*

From directory `src/python/git_cloner` run:
```bash
$ sh run.sh
```
Projects will be cloned into the subfolder `apache_repos`.

## 5. Mine pull requests (for git projects only)

*Setup*

Use Python 3 environment as described in Step 2. Also, add a new file `gh/github-api-tokens.txt`
and enter a GitHub API access token per line -- the more the better.

*Execution*

From directory `src/python/pr_downloader` run:
```bash
$ sh run.sh
```

## 6. Unmask aliases (identify unique developer IDs)
*Setup*

Use Python 3 environment as described in Step 2.

*Execution*

From directory `src/python/unmasking` run:
```bash
$ sh run.sh
```

## 7. Build developer commit history (for git projects only)
*Setup*

Use Python 3 environment as described in Step 2.

*Execution*

From directory `src/python/commit_analyzer` run:
```bash
$ sh run.sh
```

## 8. Compute developers' Big5 personality scores per month from emails (for git projects only)
*Setup*

Use Python 3 environment as described in Step 2.

*Execution*

From directory `src/python/personality_insights` run:
```bash
$ sh run.sh
```

## 9. Export results
*Setup*

Use Python 3 environment as described in Step 2.

*Execution*

From directory `src/python/export_results` run:
```bash
$ sh run.sh
```
