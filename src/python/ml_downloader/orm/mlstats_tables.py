from sqlalchemy import Column, String, BigInteger

from db.setup import Base
import sqlalchemy
from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint
from sqlalchemy import DateTime, Enum, NUMERIC, TEXT, VARCHAR
from sqlalchemy.dialects.mysql import MEDIUMTEXT

# class MailingList(Base):
#     __tablename__ = 'mailing_lists'
#
#     mailing_list_url = Column(String(255), primary_key=True)
#     mailing_list_name = Column(String(255))
#     project_name = Column(String(255))
#     last_analysis = Column(DateTime)
#
#     def __init__(self,
#                  mailing_list_url,
#                  mailing_list_name,
#                  project_name,
#                  last_analysis,
#                  ):
#         self.mailing_list_url = mailing_list_url
#         self.mailing_list_name = mailing_list_name
#         self.project_name = project_name
#         if last_analysis is not None and last_analysis != 'None':
#             st = parser.parse(last_analysis)
#             self.last_analysis = datetime.datetime(st.year, st.month, st.day, st.hour, st.minute, st.second)
#         else:
#             self.last_analysis = None
#
#
# class MailingListSender(Base):
#     __tablename__ = 'people'
#
#     email_address = Column(String(255), primary_key=True)
#     name = Column(String(255))
#     username = Column(String(255))
#     domain_name = Column(String(255))
#     top_level_domain = Column(String(255))
#
#     def __init__(self,
#                  email_address,
#                  name,
#                  username,
#                  domain_name,
#                  top_level_domain
#                  ):
#         self.email_address = email_address
#         self.name = name
#         self.username = username
#         self.domain_name = domain_name
#         self.top_level_domain = top_level_domain


class MailingListSenderId(Base):
    __tablename__ = 'people_id'

    id = Column(BigInteger)
    email_address = Column(String(255), primary_key=True)
    name = Column(String(255))
    username = Column(String(255))

    def __init__(self,
                 id,
                 email_address,
                 name,
                 username,
                 ):
        self.email_address = email_address
        self.name = name
        self.username = username
        self.id = id


# class SenderByMailingList(Base):
#     __tablename__ = 'mailing_lists_people'
#
#     email_address = Column(String(255), primary_key=True)
#     mailing_list_url = Column(String(255), primary_key=True)
#
#     def __init__(self,
#                  email_address,
#                  mailing_list_url
#                  ):
#         self.email_address = email_address
#         self.mailing_list_url = mailing_list_url
#
#
# class Message(Base):
#     __tablename__ = 'messages'
#
#     message_id = Column(String(255), primary_key=True)
#     mailing_list_url = Column(String(255), primary_key=True)
#     message_body = Column(LONGTEXT)
#     first_date = Column(DateTime)
#
#     def __init__(self,
#                  mailing_list_url,
#                  message_id,
#                  first_date,
#                  message_body
#                  ):
#         self.mailing_list_url = mailing_list_url
#         self.message_id = message_id
#         self.first_date = first_date
#         self.message_body = message_body
#
#
# class MessagePeople(Base):
#     __tablename__ = 'messages_people'
#
#     type_of_recipient = Column(Enum('To', 'From', 'Cc', 'Bcc'))
#     message_id = Column(String(255), primary_key=True)
#     mailing_list_url = Column(String(255), primary_key=True)
#     email_address = Column(String(255), primary_key=True)

"""
This module contains a the definition of the generic SQL tables used
by mlstats.
"""


def MediumText():
    return sqlalchemy.Text().with_variant(MEDIUMTEXT(), 'mysql')


class MailingLists(Base):
    __tablename__ = 'mailing_lists'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    mailing_list_url = Column(VARCHAR(255), primary_key=True)
    mailing_list_name = Column(VARCHAR(255))
    project_name = Column(VARCHAR(255))
    last_analysis = Column(DateTime)

    def __repr__(self):
        return u"<MailingLists(mailing_list_url='{0}', " \
               "mailing_list_name='{1}', project_name='{2}', " \
               "last_analysis='{3}')>".format(self.mailing_list_url,
                                              self.mailing_list_name,
                                              self.project_name,
                                              self.last_analysis)


class CompressedFiles(Base):
    __tablename__ = 'compressed_files'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    url = Column(VARCHAR(255), primary_key=True)
    mailing_list_url = Column(VARCHAR(255),
                              ForeignKey('mailing_lists.mailing_list_url'),
                              nullable=False)
    status = Column(Enum('new', 'visited', 'failed', native_enum=True,
                         name='enum_status'))
    last_analysis = Column(DateTime)

    def __repr__(self):
        return u"<CompressedFiles(url='{0}', " \
               "mailing_list_url='{1}', status='{2}' " \
               "last_analysis='{3}')>".format(self.url,
                                              self.mailing_list_url,
                                              self.status,
                                              self.last_analysis)


class People(Base):
    __tablename__ = 'people'
    __table_args__ = {'mysql_engine': 'InnoDB',
                      'mysql_charset': 'utf8mb4'}

    email_address = Column(VARCHAR(255), primary_key=True)
    name = Column(VARCHAR(255))
    username = Column(VARCHAR(255))
    domain_name = Column(VARCHAR(255))
    top_level_domain = Column(VARCHAR(255))

    def __repr__(self):
        return u"<People(email_address='{0}', name='{1}', " \
               "username='{2}' domain_name='{3}'" \
               "top_level_domain='{4}')>".format(self.email_address,
                                                 self.name,
                                                 self.username,
                                                 self.domain_name,
                                                 self.top_level_domain)


class Messages(Base):
    __tablename__ = 'messages'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    message_id = Column(VARCHAR(255), primary_key=True)
    mailing_list_url = Column(VARCHAR(255),
                              ForeignKey('mailing_lists.mailing_list_url',
                                         onupdate='CASCADE',
                                         ondelete='CASCADE'),
                              primary_key=True)
    mailing_list = Column(VARCHAR(255))
    first_date = Column(DateTime)
    first_date_tz = Column(NUMERIC(11))
    arrival_date = Column(DateTime)
    arrival_date_tz = Column(NUMERIC(11))
    subject = Column(VARCHAR(1024))
    message_body = Column(MediumText())
    is_response_of = Column(VARCHAR(255), index=True)
    mail_path = Column(TEXT)

    def __repr__(self):
        return u"<Messages(message_id='{0}', " \
               "mailing_list_url='{1}', " \
               "mailing_list='{2}', " \
               "first_date='{3}', first_date_tz='{4}', " \
               "arrival_date='{5}', arrival_date_tz='{6}', " \
               "subject='{7}', message_body='{8}', " \
               "is_response_of='{9}', " \
               "mail_path='{10}')>".format(self.message_id,
                                           self.mailing_list_url,
                                           self.mailing_list,
                                           self.first_date,
                                           self.first_date_tz,
                                           self.arrival_date,
                                           self.arrival_date_tz,
                                           self.subject,
                                           self.message_body,
                                           self.is_response_of,
                                           self.mail_path)


class MessagesPeople(Base):
    __tablename__ = 'messages_people'
    __table_args__ = (
        ForeignKeyConstraint(['message_id', 'mailing_list_url'],
                             ['messages.message_id',
                              'messages.mailing_list_url'],
                             onupdate='CASCADE',
                             ondelete='CASCADE'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    )

    type_of_recipient = Column(Enum('From', 'To', 'Cc',
                                    native_enum=True,
                                    name='enum_type_of_recipient'),
                               primary_key=True,
                               default='From')
    message_id = Column(VARCHAR(255),
                        primary_key=True,
                        index=True)
    mailing_list_url = Column(VARCHAR(255),
                              primary_key=True)
    email_address = Column(VARCHAR(255),
                           ForeignKey('people.email_address',
                                      onupdate='CASCADE',
                                      ondelete='CASCADE'),
                           primary_key=True)

    def __repr__(self):
        return u"<MessagesPeople(type_of_recipient='{0}', " \
               "message_id='{1}', " \
               "mailing_list_url='{1}', " \
               "email_address='{2}')>".format(self.type_of_recipient,
                                              self.message_id,
                                              self.mailing_list_url,
                                              self.email_address)


class MailingListsPeople(Base):
    __tablename__ = 'mailing_lists_people'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    email_address = Column(VARCHAR(255),
                           ForeignKey('people.email_address',
                                      onupdate='CASCADE',
                                      ondelete='CASCADE'),
                           primary_key=True)
    mailing_list_url = Column(VARCHAR(255),
                              ForeignKey('mailing_lists.mailing_list_url',
                                         onupdate='CASCADE',
                                         ondelete='CASCADE'),
                              primary_key=True)

    def __repr__(self):
        return u"<MailingListsPeople(email_address='{0}', " \
               "mailing_list_url='{1}')>".format(self.email_address,
                                                 self.mailing_list_url)
