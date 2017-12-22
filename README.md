# personality

## Crawl Apache projects
*Setup*

Use Python 3 environment and install packages from `src/python/apache_crawler/requirements.txt`

*Execution*

From directory `src/python/apache_crawler` run:
```bash
$ scrapy apache_crawler -t (json|csv) -o apache-projects.(json|csv) [-L DEBUG --logfile apache.log]
```

## Mine mailing lists (for git projects only)

*Setup*

Use Python 2 environment and install packages from `src/python/ml_downloader/requirements.txt`

*Execution*

From directory `src/python/ml_download` run:
```bash
$ python ml_crawler.py
```
