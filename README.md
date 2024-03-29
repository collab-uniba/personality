# Apache developers' Big-Five personality profiler [![DOI](https://zenodo.org/badge/114795784.svg)](https://zenodo.org/badge/latestdoi/114795784)

Content and scripts from this repository can be freely reused for academic purposes, provided that you cite the following paper in your work:
```
F. Calefato, F. Lanubile, and B. Vasilescu (2019) “A large-scale, in-depth analysis of developers’
personalities in the Apache ecosystem.” Information and Software Technology, Vol. 114, Oct., 
pp. 1-20, DOI: 10.1016/j.infsof.2019.05.012.
```

## 0. Dataset
The final results of the scripts (i.e., developers' monthly scores per project) are stored [here](https://github.com/collab-uniba/personality/tree/master/src/python/export_results) (see the files in CSV format). 
Instead, the entire MySQL database, containing the data scraped from the Apache website, the email archives, and the code metadata obtained from GitHub, is stored [here](https://mega.nz/#F!cJ0BiSrI!DYWcN7CbcHdSfqpuzSSmuw).

The dump can be imported into a pre-existing db named `apache` as follows:

```bash
$ mysql -u <username> -p<PlainPassword> apache < apachebig5.sql
```

Repeat the instruction above for all the `.sql` files provided.

## 1. Cloning
```bash
$ git clone https://github.com/collab-uniba/personality.git --recursive
```
## 2. Configuration
Edit the following configuration files:
* `src/python/db/cfg/setup.yml` - MySQL database configuration
```yaml
mysql:
    host: 127.0.0.1
    user: root
    passwd: *******
    db: apache
```
* `src/python/big5_personality/personality_insights/cfg/watson.yml` - IBM Watson Personality Insights (you will need to register and 
get your personal username and password)
```yaml
personality:
    username: secret-user
    password: secret-password
    version: 2017-10-13
```
* `src/python/big5_personality/liwc/cfg/receptiviti.yaml` - Receptiviti (you will need to register and 
get your personal api key and api secret key)
```yaml
receptiviti:
    baseurl: https://api-v3.receptiviti.com
    api_key: *****
    api_secret_key: *****
```

## 3. Crawl Apache projects
* *Setup*:
First, install the library [libgit2](https://libgit2.org) on your system. Then, use a Python 3 environment and install the required packages from `src/python/requirements.txt`
* *Execution*:
From directory `src/python/apache_crawler` run:
```bash
$ scrapy apache_crawler -t (json|csv) -o apache-projects.(json|csv) [-L DEBUG --logfile apache.log]
```

## 4. Mine mailing lists (for Git projects only)
* *Setup*:
Use Python 2 environment and install packages from `src/python/ml_downloader/requirements.txt`.
Then, recreate database schema as follows:
```bash
$ mysql -u<user> -p<password> apache < submodules/mlminer/db/data_model_mysql.sql
```
* *Execution*:
From directory `src/python/ml_downloader` run:
```bash
$ sh run.sh
```

## 5. Clone Git projects
* *Setup*:
Use Python 3 environment as described in Step 3.
* *Execution*:
From directory `src/python/git_cloner` run:
```bash
$ sh run.sh
```
Projects will be cloned into the subfolder `apache_repos`.

<!---
## 5. Mine pull requests (for git projects only)

*Setup*

Use Python 3 environment as described in Step 3. Also, add a new file `gh/github-api-tokens.txt`
and enter a GitHub API access token per line -- the more the better.

*Execution*

From directory `src/python/pr_downloader` run:
```bash
$ sh run.sh
```
-->
## 6. Get developers' location from GitHub
* *Setup*:
    1. In MySql command line enter following instruction:
        ```bash
        set character set utf8mb4; 
        ```
    2. Use Python 3 environment as described in Step 3. 
    3. Add a new file `github-api-tokens.txt`
and enter a GitHub API access token
* *Execution*:
From directory `src/python/github_users_location` run:
```bash
$ sh run.sh [reset]
```
where:
- reset: to empty db table containing github users location

## 7. Unmask aliases (identify unique developer IDs)
* *Setup*:
    1. Use Python 3 environment as described in Step 2.
    2. At first run, execute from dicrectory `src/python/unmasking`:
        ```bash
        $ python nltk_download.py
        ```
* *Execution*:
From directory `src/python/unmasking` run:
```bash
$ sh run.sh
```

## 8. Build developer commit history (for Git projects only)
* *Setup*:
Use Python 3 environment as described in Step 3.
* *Execution*:
From directory `src/python/commit_analyzer` run:
```bash
$ sh run.sh 
```

## 9. Compute developers' Big Five traits scores per month from emails (for Git projects only)
* *Setup*:
    1. Install NLoN package as described [here](https://github.com/M3SOulu/NLoN)
    2. Use Python 3 environment as described in Step 3.
* *Execution*:
From directory `src/python/big5_personality` run:
```bash
$ sh run.sh <tool> [reset]
```
where:
- tool: tool name, either `liwc15` or `p_insights`
- reset: to empty the db tables containing personality data before new computing

## 10. Export results
* *Setup*:
Use Python 3 environment as described in Step 3.
* *Execution*:
From directory `src/python/export_results` run:
```bash
$ sh run.sh <tool>
```
where:
- tool: tool name, with values in {`liwc07`, `liwc15`, `p_insights`}

Results are stored in files `personality_liwc.csv` and `personality_p_insights.csv`.
