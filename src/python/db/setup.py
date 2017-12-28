import logging
import os

import yaml
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

Base = declarative_base()


class SessionWrapper:
    log = logging.getLogger(__name__)
    proto = 'mysql'
    server = None
    db_name = None
    u = None
    p = None

    @staticmethod
    def load_config(config_file):
        with open(os.path.join(os.getcwd(), config_file), 'r') as config:
            cfg = yaml.load(config)
            SessionWrapper.server = cfg[SessionWrapper.proto]['host']
            SessionWrapper.db_name = cfg[SessionWrapper.proto]['db']
            SessionWrapper.u = cfg[SessionWrapper.proto]['user']
            SessionWrapper.p = cfg[SessionWrapper.proto]['passwd']
            if SessionWrapper.p != '':
                SessionWrapper.p = ':' + SessionWrapper.p

    @staticmethod
    def new(init=False):
        engine = create_engine('{0}://{1}{2}@{3}/{4}?charset=utf8mb4'.format(SessionWrapper.proto, SessionWrapper.u,
                                                                             SessionWrapper.p, SessionWrapper.server,
                                                                             SessionWrapper.db_name),
                               pool_recycle=3600)
        if not database_exists(engine.url):
            SessionWrapper.log.info("Database %s created" % SessionWrapper.db_name)
            create_database(engine.url, encoding='utf8mb4')
        SessionWrapper.log.debug(
            msg='Connection established to {0}@{1}.'.format(SessionWrapper.proto, SessionWrapper.server))

        if init:
            SessionWrapper.__init_db(engine)
            SessionWrapper.log.info(msg='Structure for database %s created.' % SessionWrapper.db_name)

        _session = sessionmaker(engine)
        return _session()

    @staticmethod
    def __init_db(engine):
        metadata = Base.metadata
        metadata.create_all(engine)
