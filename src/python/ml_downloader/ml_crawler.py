import logging

import requests

from apache_crawler.orm import ApacheProject
from orm import SessionWrapper
from pymlstats.main import Application


def get_mailing_lists():
    log.info('Retrieving Git project mailing lists')
    SessionWrapper.load_config('../apache_crawler/orm/cfg/setup.yml')
    session = SessionWrapper.new(init=False)
    mls = session.query(ApacheProject.dev_ml_url, ApacheProject.user_ml_url).filter_by(repository_type='git').all()
    log.info('Retrieved %s projects and %s mailing lists' % (len(mls), 2 * len(mls)))
    return mls


def store_mailing_lists(ml_lists, dest):
    with(open(dest, mode='w')) as f:
        for m_dev, m_user in ml_lists:
            f.write('%s\n' % m_dev)
            f.write('%s\n' % m_user)


def exclude_broken(_all, _done):
    with(open('error.mls', mode='a')) as error:
        for url in _all:
            request = requests.get(url)
            if request.status_code != 200:
                _done.append(url)
            else:
                error.write('Broken url excluded %s' % url)
    return _done


def start(mailing_lists_f):
    mls_all = list()
    with(open(mailing_lists_f, mode='r')) as f:
        for l in f:
            mls_all.append(l.strip())

    mls_done = list()
    try:
        with open('temp.mls', mode='r') as temp:
            for l in temp:
                mls_done.append(l.strip())
    except IOError:
        open('temp.mls', mode='w')

    mls_done = exclude_broken(mls_all, mls_done)

    projects_mailing_lists = [m for m in mls_all if m not in mls_done]
    if not projects_mailing_lists:
        print('All mailing lists seem to have been already mined.\n'
              'Please, manually delete file ''temp.mls'' if you want to start '
              'downloading them again.')
        return

    with(open('temp.mls', mode='a')) as temp:
        with(open('error.mls', mode='a')) as error:
            for user_dev_mls in projects_mailing_lists:
                log.info('Starting mining mailing list %s' % user_dev_mls)
                try:
                    app = Application(driver='mysql',
                                      user=SessionWrapper.u,
                                      password=SessionWrapper.p[1:],
                                      dbname=SessionWrapper.db_name,
                                      host=SessionWrapper.server,
                                      url_list=(user_dev_mls,),
                                      report_filename='mlstats-report.log',
                                      make_report=True,
                                      be_quiet=False,
                                      force=False,
                                      web_user=None,
                                      web_password=None,
                                      compressed_dir=None,
                                      backend=None,
                                      offset=0)
                    temp.write("%s\n" % user_dev_mls)
                except Exception:
                    log.error('Error parsing mailing list %s' % user_dev_mls)
                    error.write(user_dev_mls)


if __name__ == '__main__':
    logging.basicConfig()
    log = logging.getLogger('ml_crawler')
    log.setLevel(logging.DEBUG)
    try:
        mls = sorted(get_mailing_lists())
        filename = 'git-mls.txt'
        store_mailing_lists(mls, filename)

        SessionWrapper.load_config('cfg/setup.yml')
        SessionWrapper.new(init=True)

        start(filename)
    except KeyboardInterrupt:
        print >> sys.stderr, '\nReceived Ctrl-C or other break signal. Exiting.'
