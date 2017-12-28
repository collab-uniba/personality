# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ApacheCrawlerItem(scrapy.Item):
    project = scrapy.Field()
    status = scrapy.Field()
    category = scrapy.Field()
    committers = scrapy.Field()
    pmc_members = scrapy.Field()
    pmc_chair = scrapy.Field()
    url = scrapy.Field()
    language = scrapy.Field()
    repository_url = scrapy.Field()
    repository_type = scrapy.Field()
    bug_tracker_url = scrapy.Field()
    dev_ml_url = scrapy.Field()  # http://mail-archives.apache.org/mod_mbox/<project>-dev/
    user_ml_url = scrapy.Field()   # http://mail-archives.apache.org/mod_mbox/<project>-user/

    def __str__(self):
        return str(self['project'])

    __repr__ = __str__
