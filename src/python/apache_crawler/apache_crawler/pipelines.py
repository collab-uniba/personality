# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import importlib
import logging
import traceback

from sqlalchemy.orm import exc

from apache_crawler.orm.setup import SessionWrapper
from apache_crawler.orm.tables import *


class ApacheCrawlerPipeline(object):
    log = logging.getLogger(__name__)

    def process_item(self, item, spider):
        self.log.info('Finishing item %s' % item)
        try:
            item['category'].split('/category/')[1]
        except IndexError:
            pass
        item['dev_ml_url'] = 'http://mail-archives.apache.org/mod_mbox/%s-dev/' % item['project']
        item['user_ml_url'] = 'http://mail-archives.apache.org/mod_mbox/%s-user/' % item['project']
        return item


class DatabaseStoragePipeline(object):
    log = logging.getLogger(__name__)

    def process_item(self, item, spider):
        self.log.debug('Storing item %s' % item)

        session = SessionWrapper.new(init=False)

        try:
            pmc_name, pmc_login = item['pmc_chair'].split('#')
            pmc_id = self.add_developer(session, pmc_login, pmc_name)
            project_id = self.add_project(session, item, pmc_id)

            committers = item['committers'].split(',')
            for c in committers:
                c_name, c_login = c.split('#')
                c_id = self.add_developer(session, c_login, c_name)
                self.link_dev_project(session, project_id, c_id, 'apache_crawler.orm.tables', 'ProjectCommitter')

            members = item['pmc_members'].split(',')
            for m in members:
                m_name, m_login = m.split('#')
                m_id = self.add_developer(session, m_login, m_name)
                self.link_dev_project(session, project_id, m_id, 'apache_crawler.orm.tables', 'PmcMember')
        except Exception:
            self.log.error('Consistency error storing data in the database')
            traceback.print_exc()
        return item

    def add_project(self, session, item, pmc_id):
        try:
            project_id = session.query(ApacheProject.id).filter_by(name=item['project']).one().id
        except exc.NoResultFound:
            project = ApacheProject(name=item['project'],
                                    status=item['status'],
                                    category=item['category'],
                                    language=item['language'],
                                    pmc_chair=pmc_id,
                                    url=item['url'],
                                    repository_url=item['repository_url'],
                                    repository_type=item['repository_type'],
                                    bug_tracker_url=item['bug_tracker_url'],
                                    dev_ml_url=item['dev_ml_url'],
                                    user_ml_url=item['user_ml_url']
                                    )
            session.add(project)
            session.commit()
            project_id = session.query(ApacheProject.id).filter_by(name=item['project']).one().id
        return project_id

    def add_developer(self, session, login, name):
        name = name.strip()
        login = login.strip()

        try:
            dev_id = session.query(ApacheDeveloper.id).filter_by(name=name, login=login).one().id
        except exc.NoResultFound:
            developer = ApacheDeveloper(name=name, login=login)
            session.add(developer)
            session.commit()
            dev_id = session.query(ApacheDeveloper.id).filter_by(name=name, login=login).one().id
        return dev_id

    def link_dev_project(self, session, project_id, dev_id, module, class_name):
        DeveloperClass = getattr(importlib.import_module(module), class_name)

        try:
            session.query(DeveloperClass).filter_by(project_id=project_id, developer_id=dev_id).one()
        except exc.NoResultFound:
            developer = DeveloperClass(project_id=project_id, developer_id=dev_id)
            session.add(developer)
            session.commit()
            session.query(DeveloperClass).filter_by(project_id=project_id, developer_id=dev_id).one()
