import logging
import sys

import requests

from apache_projects.orm import ApacheProject
from db import SessionWrapper
from ml_downloader.orm import MailingList
from pymlstats.main import Application


def get_mailing_lists():
    log.info('Retrieving Git project mailing lists')
    SessionWrapper.load_config('../db/cfg/setup.yml')
    session = SessionWrapper.new(init=False)
    res = session.query(ApacheProject.dev_ml_url, ApacheProject.user_ml_url).filter_by(repository_type='git').all()
    mls = list()
    for r in res:
        mls.append(r[0])
        mls.append(r[1])
    log.info('%s retrieved' % len(mls))
    return mls


def store_mailing_lists(ml_lists, dest):
    with(open(dest, mode='w')) as f:
        for m_dev, m_user in ml_lists:
            f.write('%s\n' % m_dev)
            f.write('%s\n' % m_user)


def exclude_broken(_all, _done):
    log.info('Excluding mailing lists with broken archive urls')
    with(open('error.mls', mode='a')) as error:
        for url in _all:
            request = requests.get(url)
            if request.status_code != 200:
                _done.append(url)
            else:
                error.write('Broken url excluded %s' % url)
    log.info('%s excluded as done or broken' % len(_done))
    return _done


def exclude_done():
    log.info('Excluding mailing lists already analyzed')
    SessionWrapper.load_config('../db/cfg/setup.yml')
    session = SessionWrapper.new(init=True)
    done = list()
    res = session.query(MailingList.mailing_list_url).all()
    for r in res:
        done.append(r[0] + '/')
    log.info('%s excluded' % len(done))
    return done


def get_mailing_lists_to_do(_all, excluded):
    to_do = [m for m in _all if m not in excluded]
    return to_do


def start(projects_mailing_lists):
    if not projects_mailing_lists:
        print('All mailing lists seem to have been already mined.\n'
              'Please, manually delete file ''temp.mls'' if you want to start '
              'downloading them again.')
        return

    with(open('error.mls', mode='a', buffering=0)) as error:
        log.info('Starting mining mailing lists: %s' % len(projects_mailing_lists))
        try:
            Application(driver='mysql',
                        user=SessionWrapper.u,
                        password=SessionWrapper.p[1:],
                        dbname=SessionWrapper.db_name,
                        host=SessionWrapper.server,
                        url_list=projects_mailing_lists,
                        report_filename='mlstats-report.log',
                        make_report=True,
                        be_quiet=False,
                        force=False,
                        web_user=None,
                        web_password=None,
                        compressed_dir=None,
                        backend=None,
                        offset=0)
        except Exception as e:
            log.error('Error parsing mailing lists', e)
            error.write(e.message)


if __name__ == '__main__':
    logging.basicConfig()
    log = logging.getLogger('ml_crawler')
    log.setLevel(logging.DEBUG)
    try:
        mls_all = sorted(get_mailing_lists())
        mls_done_or_broken = exclude_done()
        mls_done_or_broken = exclude_broken(mls_all, mls_done_or_broken)
        mls_to_do = get_mailing_lists_to_do(mls_all, mls_done_or_broken)
        start(mls_to_do)
    except KeyboardInterrupt:
        print >> sys.stderr, '\nReceived Ctrl-C or other break signal. Exiting.'
