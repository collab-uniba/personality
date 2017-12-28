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

Use Python 2 environment and install packages from `src/python/ml_downloader/requirements.txt`

*Execution*

From directory `src/python/ml_downloader` run:
```bash
$ sh run.sh
```

## 4. Mine pull requests (for git projects only)

*Setup*
USe Python 3 environment as described in Step 2. Also, add a new file `gh/github-api-tokens.txt`
and enter a GitHub API access token per line -- the more the better.

*Execution*

From directory `src/python/pr_downloader` run:
```bash
$ sh run.sh ../path/to/git/repos
```

## 5. Build developer commit history (for git projects only)


## 6. Compute developer personality scores per month from emails (for git projects only)
