import pickle
import re
from _datetime import datetime
from itertools import groupby

from bs4 import BeautifulSoup as BS4
from sqlalchemy import or_, and_
from sqlalchemy.orm import exc
from watson_developer_cloud import WatsonException, WatsonInvalidArgument

from apache_projects.orm.apache_tables import *
from commit_analyzer.orm.commit_tables import *
from db.setup import SessionWrapper
from logger import logging_config
from ml_downloader.orm.mlstats_tables import *
from personality_insights import big5_personality
from personality_insights.orm import PersonalityProjectMonth
from unmasking.unmask_aliases import OFFSET


def get_profile(email_content):
    try:
        json_profile = big5_personality.profile(email_content, content_type='text/plain',  # text/html
                                                raw_scores=True,
                                                consumption_preferences=True)
        return json_profile
    except (WatsonException, WatsonInvalidArgument) as e:
        logger.error(e)


def clean_up(message_bodies):
    cleansed = list()
    for message_body in message_bodies:
        soup = BS4(message_body, 'html.parser')
        clean_message_body = soup.text

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


def load_alias_map(filename):
    with open(filename, "rb") as f:
        unpickler = pickle.Unpickler(f)
        alias_map = unpickler.load()
    return alias_map


def get_alias_ids(_map, uid):
    aliases = set()
    for key in _map.keys():
        if _map[key] == uid and key != uid:
            aliases.add(key)
    return list(aliases)


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


def get_personality_score_by_month(usr_emails):
    # sort emails by date
    usr_emails.sort(key=lambda e: e.first_date)
    # group by month
    usr_profile_by_month = dict()
    for month, eml_list in groupby(usr_emails, key=lambda e: datetime.strftime(e.first_date, "%Y-%m")):
        clean_emails = clean_up([x.message_body for x in eml_list])
        json_scores = get_profile('\n\n'.join(clean_emails))
        usr_profile_by_month[month] = json_scores
    return usr_profile_by_month


def reset_personality_table():
    session.query(PersonalityProjectMonth).delete()
    session.commit()


def main():
    alias_map = load_alias_map('../unmasking/idm/dict/alias_map.dict')
    reset_personality_table()

    projects = sorted(session.query(ApacheProject.name, ApacheProject.dev_ml_url, ApacheProject.user_ml_url). \
                      filter(
        and_(ApacheProject.name == GithubRepository.slug, GithubRepository.id == Commit.repo_id)).distinct().all())

    for uid in set(alias_map.values()):
        logger.info('Processing uid %s' % uid)
        # try:
        # sender_id = session.query(MailingListSenderId.id).filter_by(email_address=e.email_address).one()
        # uid = alias_map[sender_id.id]
        aliases = get_alias_ids(alias_map, uid)
        alias_email_addresses = get_alias_email_addresses(aliases + [uid, ])

        for p in projects:
            logger.debug('Processing project %s' % p.name)
            project_mailing_lists = (p.dev_ml_url[:-1], p.user_ml_url[:-1])  # remove trailing slash
            # project_mailing_lists_email_addresses = session.query(MessagesPeople.email_address).filter(
            #    or_(MessagesPeople.mailing_list_url == ml for ml in project_mailing_lists)).distinct().all()

            all_emails = get_all_emails(alias_email_addresses, project_mailing_lists)
            if all_emails:
                usr_personality_month = get_personality_score_by_month(all_emails)

                # store in table, keys: dev_uid, project_name, month
                for month, json_score in usr_personality_month.items():
                    v = PersonalityProjectMonth(dev_uid=uid, project_name=p.name, month=month,
                                                email_count=len(all_emails), word_count=json_score["word_count"],
                                                scores=json_score)
                    logger.debug('Adding %s' % v)
                    session.add(v)
                    try:
                        session.commit()
                    except Exception as e:
                        logger.error('Error storing personality scores for %s' % v, e)
                        continue
            else:
                logger.debug('No emails from %s to project \'%s\' mailing lists' % (alias_email_addresses, p.name))


if __name__ == '__main__':
    logger = logging_config.get_logger('personality_watson')
    SessionWrapper.load_config('../db/cfg/setup.yml')
    session = SessionWrapper.new(init=True)
    try:
        main()
    except KeyboardInterrupt:
        logger.error('Received Ctrl-C or other break signal. Exiting.')
