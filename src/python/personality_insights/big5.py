import logging
import re
import sys
from _datetime import datetime
from itertools import groupby

from bs4 import BeautifulSoup as BS4
from requests.exceptions import *
from sqlalchemy import func
from sqlalchemy import or_, and_
from sqlalchemy.orm import exc
from watson_developer_cloud import WatsonException, WatsonInvalidArgument

from apache_projects.orm.apache_tables import *
from commit_analyzer.orm.commit_tables import *
from commons.aliasing import load_alias_map, get_alias_ids
from db.setup import SessionWrapper
from logger import logging_config
from ml_downloader.orm.mlstats_tables import *
from personality_insights import big5_personality
from personality_insights.orm import PersonalityProjectMonth
from unmasking.unmask_aliases import OFFSET


def get_profile(email_content):
    try:
        try:
            json_profile = big5_personality.profile(email_content, content_type='text/html',  # text/plain
                                                    raw_scores=True,
                                                    consumption_preferences=True)
        except (ConnectionError, ConnectTimeout):
            logger.error('Connection error, retrying')
            try:
                json_profile = big5_personality.profile(email_content, content_type='text/html',  # text/plain
                                                        raw_scores=True,
                                                        consumption_preferences=True)
            except (ConnectionError, ConnectTimeout):
                logger.error('Connection error on retry, skipping')
                json_profile = ''
    except (WatsonException, WatsonInvalidArgument) as e:
        logger.error(e)
        json_profile = ''

    return json_profile


def clean_up(message_bodies):
    cleansed = list()
    for message_body in message_bodies:
        try:
            soup = BS4(message_body, 'html.parser')
            clean_message_body = soup.text
        except Exception as e:
            logger.error('Error with BS4 on text:\n\n%s\n\n' % message_body, e)
            clean_message_body = message_body

        clean_message_body = re.sub(r'^\s*>+( .*)?', '', clean_message_body, flags=re.MULTILINE)
        # clean_message_body = re.sub(r'^\s*\$+( .*)?', '', clean_message_body, flags=re.MULTILINE)
        clean_message_body = re.sub(r'^\s*\+', '', clean_message_body, flags=re.MULTILINE)
        clean_message_body = re.sub(r'^\s*---\+', '', clean_message_body, flags=re.MULTILINE)
        # dates
        clean_message_body = re.sub(r'https?:\/\/\S*', '', clean_message_body, flags=re.MULTILINE)
        clean_message_body = re.sub(r'[\w\.-]+ @ [\w\.-]+', '', clean_message_body, flags=re.MULTILINE)
        clean_message_body = re.sub(r'On .* wrote:.*', '', clean_message_body, flags=re.MULTILINE)
        clean_message_body = re.sub(r'\n[\t\s]*\n+', '', clean_message_body, flags=re.MULTILINE)
        clean_message_body = re.sub(r'[\n+]Sent from', '', clean_message_body, flags=re.MULTILINE)
        clean_message_body = re.sub(r'({+|}+|\++|_+|=+|-+|\*|\\+|/+|@+|\[+|\]+|:+|<+|>+|\(+|\)+)', '',
                                    clean_message_body, flags=re.MULTILINE)

        # clean_message_body = clean_message_body.encode('utf-8').strip()
        cleansed.append(clean_message_body.strip())
    return cleansed


def get_alias_email_addresses(alias_ids):
    alias_email_addresses = set()

    for alias_id in alias_ids:
        if alias_id > 0:
            if alias_id < OFFSET:
                # from GithubDeveloper - local_developers
                try:
                    res = session.query(GithubDeveloper.email).filter_by(id=alias_id).one()
                    alias_email_addresses.add(res.email)
                except (exc.NoResultFound, exc.MultipleResultsFound):
                    continue
            else:  # from MailingListSenderId - people_id
                try:
                    res = session.query(MailingListSenderId.email_address).filter_by(id=alias_id).one()
                    alias_email_addresses.add(res.email_address)
                except (exc.NoResultFound, exc.MultipleResultsFound):
                    continue

    return list(alias_email_addresses)


def get_all_emails(email_addresses, mailing_lists):
    # for address in email_addresses:
    res = session.query(Messages.first_date, Messages.message_body).filter(
        and_(or_(Messages.mailing_list_url == ml for ml in mailing_lists),
             or_(MessagesPeople.email_address == e for e in email_addresses))).distinct().all()
    return res


def get_personality_score_by_month(uid, p_name, usr_emails, resume_month):
    # sort emails by date
    usr_emails.sort(key=lambda e: e.first_date)
    # group by month
    for month, eml_list in groupby(usr_emails, key=lambda e: datetime.strftime(e.first_date, "%Y-%m")):
        if resume_month is not None and month <= resume_month:
            continue
        logger.debug('Processing month %s' % month)
        clean_emails = clean_up([x.message_body for x in eml_list])
        json_score = get_profile('\n\n'.join(clean_emails))
        # store in table; keys: dev_uid, project_name, month
        if json_score is not None and json_score != '':
            word_count = json_score['word_count']
        else:
            word_count = 0
        v = PersonalityProjectMonth(dev_uid=uid, project_name=p_name, month=month,
                                    email_count=len(usr_emails), word_count=word_count,
                                    scores=json_score)
        logger.debug('Adding %s' % v)
        session.add(v)
        try:
            session.commit()
        except Exception as e:
            logger.error('Error storing personality scores for %s' % v, e)
            continue


def reset_personality_table():
    session.query(PersonalityProjectMonth).delete()
    session.commit()


def already_parsed_uid_project_month(ids, p_name):
    res = session.query(func.max(PersonalityProjectMonth.month)).filter(
        and_(or_(PersonalityProjectMonth.dev_uid == _id for _id in ids),
             PersonalityProjectMonth.project_name == p_name)).all()
    month = res[0][0]
    return month


def already_parsed_uid_project(ids):
    res = session.query(PersonalityProjectMonth.project_name).filter(
        or_(PersonalityProjectMonth.dev_uid == _id for _id in ids)).order_by(
        PersonalityProjectMonth.project_name.desc()).all()
    if res:
        p_name = res[0][0]
    else:
        p_name = None
    return p_name


def already_parsed_uid(ids):
    res = session.query(func.max(PersonalityProjectMonth.dev_uid)).filter(
        or_(PersonalityProjectMonth.dev_uid == _id for _id in ids)).all()
    uid = res[0][0]
    return uid


def main():
    alias_map = load_alias_map('../unmasking/idm/dict/alias_map.dict')

    projects = sorted(session.query(ApacheProject.name, ApacheProject.dev_ml_url, ApacheProject.user_ml_url). \
                      filter(
        and_(ApacheProject.name == GithubRepository.slug, GithubRepository.id == Commit.repo_id)).distinct().all())

    for uid in sorted(set(alias_map.values())):
        aliases = sorted(get_alias_ids(alias_map, uid) + [uid, ])
        # negative ids for ASFers
        # positive for git developers
        # positive, starts from OFFSET ids for emailers
        resume_id = already_parsed_uid(aliases)
        if resume_id is not None and uid < resume_id:
            logger.debug('%s already analyzed, skipping' % uid)
            continue

        alias_email_addresses = get_alias_email_addresses(aliases)
        if not alias_email_addresses:
            logger.debug('%s has no email addresses associated, skipping' % uid)
            continue
        logger.info('Processing uid %s <%s>' % (uid, ','.join(alias_email_addresses)))

        for p in projects:
            resume_project = already_parsed_uid_project(aliases)
            if resume_project is not None and p.name < resume_project:
                continue
            logger.info('Processing project %s' % p.name)
            project_mailing_lists = (p.dev_ml_url[:-1], p.user_ml_url[:-1])  # remove trailing slash
            # project_mailing_lists_email_addresses = session.query(MessagesPeople.email_address).filter(
            #    or_(MessagesPeople.mailing_list_url == ml for ml in project_mailing_lists)).distinct().all()

            logger.debug('Retrieving emails from %s' % ', '.join(alias_email_addresses))
            all_emails = get_all_emails(alias_email_addresses, project_mailing_lists)
            if all_emails:
                resume_month = already_parsed_uid_project_month(aliases, p.name)
                get_personality_score_by_month(uid, p.name, all_emails, resume_month)
            else:
                logger.debug(
                    'No emails from %s <%s> to project \'%s\' mailing lists' % (uid, alias_email_addresses, p.name))

            logger.info('Done processing project %s' % p.name)


if __name__ == '__main__':
    logger = logging_config.get_logger('personality_watson', console_level=logging.DEBUG)
    SessionWrapper.load_config('../db/cfg/setup.yml')
    session = SessionWrapper.new(init=True)
    if len(sys.argv) > 1 and sys.argv[1] == 'reset':
        reset_personality_table()
    try:
        main()
    except KeyboardInterrupt:
        logger.error('Received Ctrl-C or other break signal. Exiting.')
