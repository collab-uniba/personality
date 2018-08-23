import logging
import sys

from github import Github
from github.GithubException import *
from sqlalchemy.exc import IntegrityError

from db.setup import SessionWrapper
from github_users_location.orm.users_location_table import UsersLocation
from logger import logging_config
from pr_downloader.orm.github_tables import PullRequest


def get_github_users():
    q1 = session.query(PullRequest.created_by_login).distinct()
    q2 = session.query(PullRequest.closed_by_login).distinct()
    q3 = session.query(PullRequest.merged_by_login).distinct()
    q4 = session.query(PullRequest.assignee_login).distinct()

    return q1.union(q2).union(q3).union(q4)


def save_user_info(username):
    try:
        github_user_profile = g.get_user(username)
        user_info = UsersLocation(username=username,
                                  location=github_user_profile.location,
                                  bio=github_user_profile.bio,
                                  company=github_user_profile.company)

        session.add(user_info)
        session.commit()
        logger.info('Done user: %s' % username)
    except UnknownObjectException:
        logger.error('User %s not found' % username)
    except IntegrityError:
        logger.info('Already parsed user: %s' % username)
        session.rollback()


def already_parsed_users():
    return session.query(UsersLocation).count()


def reset_users_location_table():
    session.query(UsersLocation).delete()
    session.commit()
    logger.info('Done resetting table')


if __name__ == '__main__':
    logger = logging_config.get_logger('users_location', console_level=logging.DEBUG)
    SessionWrapper.load_config('../db/cfg/setup.yml')
    session = SessionWrapper.new(init=True)

    if len(sys.argv) > 1 and sys.argv[1] == 'reset':
        reset_users_location_table()

    try:
        already_parsed_users = already_parsed_users()

        token = open("github-api-tokens.txt", "r").readline()
        g = Github(token)

        count_users = 0
        for user in get_github_users():
            if count_users == already_parsed_users:
                if user.created_by_login is not None and user.created_by_login != 'asfgit':
                    save_user_info(user.created_by_login)
            else:
                logger.info('Already parsed user: %s' % user.created_by_login)
                count_users += 1
    except KeyboardInterrupt:
        logger.error('Received Ctrl-C or other break signal. Exiting.')
