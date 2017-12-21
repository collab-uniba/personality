# -*- coding: utf-8 -*-
import logging

import scrapy
from bs4 import BeautifulSoup
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from apache_crawler.items import ApacheCrawlerItem

import re

class ApacheSpider(CrawlSpider):
    name = 'apache_crawler'
    allowed_domains = ['apache.org']
    start_urls = ['https://projects.apache.org/projects.html']

    rules = (
        Rule(LinkExtractor(allow=r'projects\.html\?committee'), callback='parse_project_list', follow=True),
    )

    def __init__(self, browser='PhantomJS', *a, **kw):
        super(ApacheSpider, self).__init__(*a, **kw)
        if browser == "PhantomJS":
            self.driver = webdriver.PhantomJS()
        elif browser == "Chrome":
            options = webdriver.ChromeOptions()
            options.add_argument('--ignore-certificate-errors')
            options.add_argument("--test-type")
            self.driver = webdriver.Chrome(chrome_options=options)
        self.log = logging.getLogger(__name__)

    def parse_project_list(self, response):
        self.driver.get(response.url)
        # explicit wait for page to load
        try:
            WebDriverWait(self.driver, 60).until(expected_conditions.visibility_of_element_located(
                (By.XPATH, '//div[@id="list"]/ul/li//a')))
        except TimeoutException:
            self.log.error('Timeout error waiting for resolution of {0}'.format(response.url))
            return
        try:
            hrefs = scrapy.Selector(text=self.driver.page_source).xpath('//div[@id="list"]/ul/li//a/@href').extract()
        except NoSuchElementException:
            self.log.error('Unexpected structure error on page %s' % response.url)
            return
        for target_url in hrefs:
            target_url = response.urljoin(target_url.strip())
            if 'project.html?' in target_url:
                yield scrapy.Request(target_url, callback=self.parse_project)

    def _find_index(self, val, keys):
        index = -1
        found = False
        for k in keys:
            if not found:
                index += 1
                if val in k:
                    found = True
                    break

        if not found:
            index = -1
        return index

    def parse_project(self, response):
        self.log.debug("Parsing project page %s" % response.url)

        try:
            self.driver.get(response.url)
            WebDriverWait(self.driver, 60).until(
                expected_conditions.visibility_of_element_located((By.XPATH, '//div[@id="contents"]//ul/li/b')))
            #WebDriverWait(self.driver, 120).until(lambda d: d.execute_script('return document.readyState') == 'complete')

            bs = BeautifulSoup(self.driver.page_source, 'lxml')
            i = ApacheCrawlerItem()
            i['category'] = bs.find('b', text='Category:').parent.a.text
            i['url'] = bs.find('b', text='Website:').parent.a.text
            i['status'] = bs.find('b', text='Project status:').parent.span.text
            i['language'] = bs.find('b', text='Programming language:').parent.a.text
            i['bug_tracker_url'] = bs.find('b', text='Bug-tracking:').parent.a.text
            i['repository_url'] = bs.find('b', text=re.compile('.* repository:')).parent.a.text
            if 'http://svn' in i['repository_url']:
                i['repository_type'] = 'svn'
            elif '.git' in i['repository_url']:
                i['repository_type'] = 'git'
            i['project'] = response.url.split('?')[1]

            committee_url = bs.find('div', {'id': 'contents'}).next.font.a['href'].strip()
            committee_url = response.urljoin(committee_url)
            i = self._parse_commitee(committee_url, i)
            yield i
        except IndexError:
            self.log.error('Project %s is missing description information, skipped' % response.url.split('?')[1])
        except (TimeoutException, WebDriverException):
            self.log.error('Timeout error waiting for resolution of {0}'.format(response.url))
            self.driver.save_screenshot('%-screenshot.png' % response.url.split('?')[1])
        except NoSuchElementException:
            self.log.error('XPath error parsing url %s' % response.url)

    def _parse_commitee(self, committee_url, item):
        self.log.debug("Parsing committee page %s" % committee_url)

        try:
            self.driver.get(committee_url)
            WebDriverWait(self.driver, 180).until(
                expected_conditions.visibility_of_element_located(
                    (By.XPATH, '//div[@id="contents"]//ul/li//blockquote')))
            keys = scrapy.Selector(text=self.driver.page_source).xpath(
                '//div[@id="contents"]//ul/li/b/text()').extract()
            hrefs = scrapy.Selector(text=self.driver.page_source).xpath(
                '//div[@id="contents"]//ul/li/a/@href').extract()
            values = scrapy.Selector(text=self.driver.page_source).xpath(
                '//div[@id="contents"]//ul/li/a/text()').extract()
            uid = hrefs[1].split('uid=')[1]
            item['pmc_chair'] = '{0} # {1}'.format(values[1], uid)

            lists = scrapy.Selector(text=self.driver.page_source).xpath(
                '//div[@id="contents"]//ul/li//blockquote').extract()
            pmc_names = BeautifulSoup(lists[0], 'lxml').find_all('a', {'class': {'committer', 'member'}})

            tmp = list()
            for name in pmc_names:
                tmp.append('{0} # {1}'.format(name.get_text(), name['title']))
            item['pmc_members'] = ','.join(tmp)

            committers = BeautifulSoup(lists[1], 'lxml').find_all('a', {'class': {'committer', 'member'}})
            tmp = list()
            for committer in committers:
                tmp.append('{0} # {1}'.format(committer.get_text(), committer['title']))
            item['committers'] = ','.join(tmp)

        except (TimeoutException, WebDriverException):
            self.log.error('Timeout error waiting for resolution of {0}'.format(committee_url))
            self.driver.save_screenshot('%-screenshot.png' % committee_url.split('?')[1])
        except NoSuchElementException:
            self.log.error('XPath error parsing url %s' % committee_url)
        return item
