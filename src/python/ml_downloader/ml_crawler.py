import logging
import sys

from orm import SessionWrapper
from orm import ApacheProject
from mlminer.pymlstats import Application


def get_mailing_lists():
    log.info('Retrieving Git project mailing lists')
    SessionWrapper.load_config('../apache_crawler/orm/cfg/setup.yml')
    session = SessionWrapper.new(init=False)
    mls = session.query(ApacheProject.dev_ml_url, ApacheProject.user_ml_url).filter_by(repository_type='git').all()
    log.debug('Retrieved %s projects and %s mailing lists' % (len(mls), 2 * len(mls)))
    return mls


def store_mailing_lists(ml_lists, dest):
    with(open(file=dest, mode='r')) as f:
        f.writelines(ml_lists)


def start(mailing_lists_f):
    mls_all = list()
    with(open(file=mailing_lists_f, mode='r')) as f:
        for l in f:
            mls_all.append(l)

    mls_done = list()
    with open(file='temp.mls', mode='a') as temp:
        for l in temp:
            mls_done.append(l)

    projects_mailing_lists = [m for m in mls_all if m not in mls_done]
    if not projects_mailing_lists:
        print('All mailing lists seem to have been already parsed.'
              'Please, manually delete file ''temp.mls'' if you want to start'
              'downloading them again.')
        return

    temp = open(file='temp.mls', mode='a')
    error = open(file='error.mls', mode='a')
    for user_dev_mls in projects_mailing_lists:
        log.info('Starting mining mailing lists %s' % str(user_dev_mls))
        try:
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
            temp.write("%s\n" % user_dev_mls)
        except Exception as e:
            log.error('Error parsing mailing list %s' % user_dev_mls)
            error.write(user_dev_mls)

        error.close()
        temp.close()


if __name__ == '__main__':
    log = logging.getLogger('ml_crawler')
    try:
        mls = get_mailing_lists()
        filename = 'git-mls.txt'
        store_mailing_lists = (mls, filename)

        SessionWrapper.load_config('cfg/setup.yml')
        SessionWrapper.new(init=True)

        start(filename)
    except KeyboardInterrupt:
        print ("\nReceived Ctrl-C or other break signal. Exiting.", file=sys.stderr)

