# Apache developers Big-Five personality profiler

## 1. Cloning
```bash
$ git clone https://github.com/collab-uniba/personality.git --recursive
```
## 2. Configuration
Edit the following configuration files:
* `/src/python/db/cfg/setup.yaml` - MySQL database configuration
```yaml
mysql:
    host: 127.0.0.1
    user: root
    passwd: *******
    db: apache
```
* `./src/python/personality_insights/cfg/watson.yaml` - IBM Watson Personality Insights (you will need to register and 
get your personal username and password)
```yaml
personality:
    username: secret-user
    password: secret-password
    version: 2017-10-13
```

## 3. Crawl Apache projects

*Setup*

Use Python 3 environment and install packages from `src/python/requirements.txt`

*Execution*

From directory `src/python/apache_crawler` run:
```bash
$ scrapy apache_crawler -t (json|csv) -o apache-projects.(json|csv) [-L DEBUG --logfile apache.log]
```

## 4. Mine mailing lists (for git projects only)

*Setup*

Use Python 2 environment and install packages from `src/python/ml_downloader/requirements.txt`.
Then, recreate database schema as follows:
```bash
$ mysql -u<user> -p<password> apache < submodules/mlminer/db/data_model_mysql.sql
```

*Execution*

From directory `src/python/ml_downloader` run:
```bash
$ sh run.sh
```

## 5. Clone git projects

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
