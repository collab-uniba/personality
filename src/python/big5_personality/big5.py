import logging
import re
import sys
from datetime import datetime
from itertools import groupby

from bs4 import BeautifulSoup as BS4
from sqlalchemy import exc
from sqlalchemy import func
from sqlalchemy import or_, and_
from sqlalchemy import orm

from apache_projects.orm.apache_tables import *
from big5_personality.liwc.liwc_big5 import get_profile_liwc
from big5_personality.liwc.orm.liwc_tables import LiwcScores, LiwcProjectMonth
from big5_personality.liwc.scores import get_scores
from big5_personality.personality_insights.orm import PersonalityProjectMonth
from big5_personality.personality_insights.p_insights_big5 import get_profile_insights
from commit_analyzer.orm.commit_tables import *
from commons.aliasing import load_alias_map, get_alias_ids
from db.setup import SessionWrapper
from history_analyzer.orm import CommitHistoryDevProject
from logger import logging_config
from ml_downloader.orm.mlstats_tables import *
from unmasking.unmask_aliases import EMAILERS_OFFSET

from rpy2.robjects.packages import importr
import rpy2.robjects as robjects


def training_nlon():
    nlon = importr('NLoN')
    robjects.r['load']("training_data.rda")

    return nlon, nlon.NLoNModel(robjects.r['text'], robjects.r['rater'])


def clean_up(message_bodies, nlon, nlon_model):
    cleansed = list()
    words_number = 0
    words_limit = 10000
    for message_body in message_bodies:
        try:
            soup = BS4(message_body, 'html.parser')
            clean_message_body = soup.text
        except Exception as e:
            logger.error('Error with BS4 on text:\n\n%s\n\n' % message_body, str(e))
            clean_message_body = message_body.strip()

        clean_message_body = re.sub(r'^\s*>+( .*)?', '', clean_message_body, flags=re.MULTILINE)
        clean_message_body = re.sub(r'^\s*\+', '', clean_message_body, flags=re.MULTILINE)
        clean_message_body = re.sub(r'^\s*---\+', '', clean_message_body, flags=re.MULTILINE)
        clean_message_body = re.sub(r'\n[\t\s]*\n+', '', clean_message_body, flags=re.MULTILINE)
        clean_message_body = re.sub(r'({+|}+|\++|_+|=+|-+|\*|\\+|/+|@+|\[+|\]+|:+|<+|>+|\(+|\)+)', '',
                                    clean_message_body, flags=re.MULTILINE)
        clean_message_body = re.sub(r'On\s(.[^\sw]*\s)*wrote', '', clean_message_body, flags=re.MULTILINE)
        clean_message_body = re.sub(r'[\n+]Sent from', '', clean_message_body, flags=re.MULTILINE)
        clean_message_body = re.sub(r'https?:\/\/\S*', '', clean_message_body, flags=re.MULTILINE)
        clean_message_body = re.sub(r'[\w\.-]+ @ [\w\.-]+', '', clean_message_body, flags=re.MULTILINE)
        # clean_message_body = clean_message_body.encode('utf-8').strip()

        message_by_lines = clean_message_body.splitlines()
        list_length = len(message_by_lines)
        index = 0
        for count in range(0, list_length):
            text = robjects.StrVector([message_by_lines[index]])
            if nlon.NLoNPredict(nlon_model, text)[0] == 'Not':
                del message_by_lines[index]
            else:
                index = index + 1
        clean_message_body = '\n'.join(message_by_lines)

        split_message = clean_message_body.split()
        words_number += len(split_message)
        if words_number > words_limit:
            split_message = split_message[:(words_limit - words_number)]
            clean_message_body = ' '.join(split_message)
            cleansed.append(clean_message_body.strip())
            break
        cleansed.append(clean_message_body.strip())
    return cleansed


def get_alias_email_addresses(alias_ids):
    alias_email_addresses = set()

    for alias_id in alias_ids:
        if alias_id > 0:
            if alias_id < EMAILERS_OFFSET:
                # from GithubDeveloper - local_developers
                try:
                    res = session.query(GithubDeveloper.email).filter_by(id=alias_id).one()
                    alias_email_addresses.add(res.email)
                except (orm.exc.NoResultFound, orm.exc.MultipleResultsFound):
                    continue
            else:  # from MailingListSenderId - people_id
                try:
                    res = session.query(MailingListSenderId.email_address).filter_by(id=alias_id).one()
                    alias_email_addresses.add(res.email_address)
                except (orm.exc.NoResultFound, orm.exc.MultipleResultsFound):
                    continue

    return list(alias_email_addresses)


def get_all_emails(email_addresses, mailing_lists):
    # for address in email_addresses:
    res = session.query(MessagesPeople.message_id, Messages.subject, Messages.first_date,
                        Messages.message_body).filter_by(type_of_recipient='From',
                                                         message_id=Messages.message_id).filter(
        and_(or_(MessagesPeople.email_address == e for e in email_addresses),
             or_(Messages.mailing_list_url == ml for ml in mailing_lists))).distinct().all()
    return res


def get_score_by_month(uid, p_name, usr_emails, resume_month, nlon, nlon_model):
    liwc_errors = False
    # sort emails by date
    usr_emails.sort(key=lambda e: e.first_date)
    # group by month
    for month, eml_list in groupby(usr_emails, key=lambda e: datetime.strftime(e.first_date, "%Y-%m")):
        if resume_month is not None and month <= resume_month:
            continue
        logger.debug('Cleaning up email bodies')
        clean_emails = clean_up([x.message_body for x in eml_list], nlon, nlon_model)
        if tool == 'p_insights':
            logger.info('Getting personality scores for month %s' % month)
            json_score = get_profile_insights(logger, '\n\n'.join(clean_emails))
            # store in table; keys: dev_uid, project_name, month
            if json_score is not None and json_score != '':
                word_count = json_score['word_count']
            else:
                word_count = 0
            v = PersonalityProjectMonth(dev_uid=uid, project_name=p_name, month=month,
                                        email_count=len(clean_emails), word_count=word_count,
                                        scores=json_score)
            logger.debug('Adding %s' % v)
            session.add(v)
            try:
                session.commit()
                del v
                del json_score
                del clean_emails
            except exc.IntegrityError:
                logger.warning('Duplicate entry for %s, rolling back session and keep going', v)
                session.rollback()
            except Exception as e:
                logger.error('Unknown error storing personality scores for %s\n\n' % v, e)
                continue
        elif tool == 'liwc':
            logger.info('Getting liwc scores for month %s' % month)
            liwc_errors = get_scores(logger, session, uid, p_name, month, '\n\n'.join(clean_emails), len(clean_emails))
            del clean_emails
            if liwc_errors:
                break
    return liwc_errors


def reset_personality_table():
    if tool == 'p_insights':
        session.query(PersonalityProjectMonth).delete()
    elif tool == 'liwc':
        session.query(LiwcScores).delete()
        session.query(LiwcProjectMonth).delete()
    session.commit()
    logger.info('Done resetting table %s' % tool)


def already_parsed_uid_project_month(ids, p_name):
    res = None
    if tool == 'p_insights':
        res = session.query(func.max(PersonalityProjectMonth.month)).filter(
            and_(or_(PersonalityProjectMonth.dev_uid == _id for _id in ids),
                 PersonalityProjectMonth.project_name == p_name)).all()
    elif tool == 'liwc':
        res = session.query(func.max(LiwcScores.month)).filter(
            and_(or_(LiwcScores.dev_uid == _id for _id in ids),
                 LiwcScores.project_name == p_name)).all()
    month = None
    if res:
        month = res[0][0]
    return month


def already_parsed_uid_project(ids):
    res = None
    if tool == 'p_insights':
        res = session.query(PersonalityProjectMonth.project_name).filter(
            or_(PersonalityProjectMonth.dev_uid == _id for _id in ids)).order_by(
                PersonalityProjectMonth.project_name.desc()).distinct().all()
    elif tool == 'liwc':
        res = session.query(LiwcScores.project_name).filter(
            or_(LiwcScores.dev_uid == _id for _id in ids)).order_by(
                LiwcScores.project_name.desc()).distinct().all()
    if res:
        p_name = res[0][0]
    else:
        p_name = None
    return p_name


def already_parsed_uid():
    res = None
    if tool == 'p_insights':
        res = session.query(func.max(PersonalityProjectMonth.dev_uid)).all()
    elif tool == 'liwc':
        res = session.query(func.max(LiwcScores.dev_uid)).all()
    uid = None
    if res:
        uid = res[0][0]
    return uid


def main():
    logger.info('Training nlon model')
    nlon, nlon_model = training_nlon()

    alias_map = load_alias_map('../unmasking/idm/dict/alias_map.dict')

    projects = sorted(session.query(ApacheProject.name, ApacheProject.dev_ml_url, ApacheProject.user_ml_url). \
                      filter(
        and_(ApacheProject.name == GithubRepository.slug, GithubRepository.id == Commit.repo_id)).distinct().all())

    contributors = session.query(CommitHistoryDevProject).order_by(CommitHistoryDevProject.dev_uid).distinct().all()

    contributors_set = sorted(set([alias_map[x.dev_uid] for x in contributors]))

    resume_id = already_parsed_uid()
    for uid in sorted(set(alias_map.values())):
        # negative ids for ASFers
        # positive for git developers
        # positive, starts from EMAILERS_OFFSET ids for emailers
        if resume_id is not None and uid < resume_id:
            logger.debug('%s already analyzed, skipping' % uid)
            continue
        if uid not in contributors_set:
            logger.debug('%s did not contribute to any project\'s code base, skipping' % uid)
            continue

        aliases = sorted(get_alias_ids(alias_map, uid) + [uid, ])
        alias_email_addresses = get_alias_email_addresses(aliases)
        if not alias_email_addresses:
            logger.debug('%s has no email addresses associated, skipping' % uid)
            continue
        logger.info('Processing uid %s <%s>' % (uid, ','.join(alias_email_addresses)))

        resume_project = already_parsed_uid_project(aliases)
        for p in projects:
            if resume_project is not None and p.name < resume_project:
                continue
            logger.info('Processing project %s' % p.name)
            project_mailing_lists = (p.dev_ml_url[:-1], p.user_ml_url[:-1])  # remove trailing slash
            # project_mailing_lists_email_addresses = session.query(MessagesPeople.email_address).filter(
            #    or_(MessagesPeople.mailing_list_url == ml for ml in project_mailing_lists)).distinct().all()

            logger.debug('Retrieving emails from %s' % ', '.join(alias_email_addresses))
            all_emails = get_all_emails(alias_email_addresses, project_mailing_lists)
            liwc_errors = False
            if all_emails:
                resume_month = already_parsed_uid_project_month(aliases, p.name)
                liwc_errors = get_score_by_month(uid, p.name, all_emails, resume_month, nlon, nlon_model)
                del all_emails
            else:
                logger.debug(
                    'No emails from %s <%s> to project \'%s\' mailing lists' % (uid, alias_email_addresses, p.name))
            logger.info('Done processing project %s' % p.name)
            if liwc_errors:
                return True
    return False


if __name__ == '__main__':
    logger = logging_config.get_logger('big5_personality', console_level=logging.DEBUG)
    SessionWrapper.load_config('../db/cfg/setup.yml')
    session = SessionWrapper.new(init=True)

    if len(sys.argv) >= 2:
        tool = sys.argv[1]
    else:
        logger.error('Missing mandatory first param for tool: \'liwc\' or \'p_insights\' expected')
        sys.exit(-1)

    if len(sys.argv) > 2 and sys.argv[2] == 'reset':
        reset_personality_table()
    try:
        """ boolean var storing presence of liwc errors """
        liwc_errors = main()
        if tool == 'liwc':
            if not liwc_errors:
                get_profile_liwc(session, logger)
                logger.info('Done getting personality scores')
            else:
                logger.error('Cannot compute LIWC personality score due to errors')
    except KeyboardInterrupt:
        logger.error('Received Ctrl-C or other break signal. Exiting.')
