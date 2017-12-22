import logging
import sys

from orm import SessionWrapper
from orm.apache_tables import ApacheProject
from pymlstats import Application


def get_mailing_lists():
    log.info('Retrieving Git project mailing lists')
    SessionWrapper.load_config('../apache_crawler/apache_crawler/cfg/setup.yml')
    session = SessionWrapper.new(init=True)
    mls = session.query(ApacheProject.dev_ml_url, ApacheProject.user_ml_url).filter_by(repository_type='git').all()
    log.debug('Retrieved %s projects and %s mailing lists' % (len(mls), 2 * len(mls)))
    return mls


def start(projects_mailing_lists):
    SessionWrapper.load_config('cfg/setup.yml')
    SessionWrapper.new(init=True)

    for user_dev_mls in projects_mailing_lists:
        log.info('Starting mining mailing lists %s' % str(user_dev_mls))
        Application(driver='mysql',
                    user=SessionWrapper.u,
                    password=SessionWrapper.p[1:],
                    dbname=SessionWrapper.db_name,
                    host=SessionWrapper.server,
                    url_list=user_dev_mls,
                    report_filename='mlstats-report.log',
                    make_report=True,
                    be_quiet=False,
                    force=False,
                    web_user=None,
                    web_password=None,
                    compressed_dir=None,
                    backend=None,
                    offset=0)


if __name__ == '__main__':
    log = logging.getLogger('ml_crawler')
    try:
        start(get_mailing_lists())
    except KeyboardInterrupt:
        print >>sys.stderr, "\nReceived Ctrl-C or other break signal. Exiting."

