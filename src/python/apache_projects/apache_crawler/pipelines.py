# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import importlib
import logging
import traceback

from scrapy.exceptions import DropItem
from sqlalchemy.orm import exc

from apache_projects.orm.apache_tables import *
from db.setup import SessionWrapper


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
        if item['project'] == 'undefined':
            raise DropItem('Dropping invalid an item with missing project name (%s)' % item['url'])
        return item


class DatabaseStoragePipeline(object):
    log = logging.getLogger(__name__)

    def process_item(self, item, spider):
        self.log.debug('Storing item %s' % item)

        session = SessionWrapper.new(init=False)

        try:
            try:
                pmc_name, pmc_login = item['pmc_chair'].split('#')
                self.add_developer(session, pmc_login, pmc_name)
            except KeyError:
                self.log.warning('PCM chair missing for project %s' & item['project'])
                pmc_login = 'undefined'
            project_id = self.add_project(session, item, pmc_login)

            committers = item['committers'].split(',')
            for c in committers:
                c_name, c_login = c.split('#')
                c_id = self.add_developer(session, c_login, c_name)
                self.link_dev_project(session, project_id, c_id, 'orm.apache_tables', 'ProjectCommitter')

            members = item['pmc_members'].split(',')
            for m in members:
                m_name, m_login = m.split('#')
                m_id = self.add_developer(session, m_login, m_name)
                self.link_dev_project(session, project_id, m_id, 'orm.apache_tables', 'PmcMember')
        except KeyError:
            self.log.error('Structural error found prepping to store item %s' % item['project'])
            traceback.print_exc()
            raise DropItem('Dropping item with invalid structure %s' % item['project'])
        except Exception:
            self.log.error('Consistency error storing data for %s in the database' % item['project'])
            traceback.print_exc()
            raise DropItem('Dropping item with invalid structure %s' % item['project'])
        return item

    def add_project(self, session, item, pmc_login):
        try:
            project = session.query(ApacheProject).filter_by(name=item['project']).one()
        except exc.NoResultFound:
            project = ApacheProject(name=item['project'],
                                    status=item['status'],
                                    category=item['category'],
                                    language=item['language'],
                                    pmc_chair=pmc_login,
                                    url=item['url'],
                                    repository_url=item['repository_url'],
                                    repository_type=item['repository_type'],
                                    bug_tracker_url=item['bug_tracker_url'],
                                    dev_ml_url=item['dev_ml_url'],
                                    user_ml_url=item['user_ml_url']
                                    )
            session.add(project)
            session.commit()

        return project.id

    def add_developer(self, session, login, name):
        name = name.strip()
        login = login.strip()

        try:
            developer = session.query(ApacheDeveloper).filter_by(login=login).one()
            if developer.name == 'undefined' and name != 'undefined':
                self.log.debug('Updating name for developer %s' % login)
                developer.name = name
                session.commit()
        except exc.NoResultFound:
            developer = ApacheDeveloper(name=name, login=login)
            session.add(developer)
            session.commit()

        return developer.id

    def link_dev_project(self, session, project_id, dev_id, module, class_name):
        Class = getattr(importlib.import_module(module), class_name)

        try:
            session.query(Class).filter_by(project_id=project_id, developer_id=dev_id).one()
        except exc.NoResultFound:
            instance = Class(project_id=project_id, developer_id=dev_id)
            session.add(instance)
            session.commit()
