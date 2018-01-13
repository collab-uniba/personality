# __all__ = ['mlstats_tables', 'MailingList', 'MailingListSender', 'MailingListSenderId', 'SenderByMailingList',
#           'Message', 'MessagePeople']

__all__ = ['mlstats_tables', 'MailingListSenderId'] + ['Base', 'MailingLists', 'CompressedFiles', 'People',
                                                       'Messages', 'MessagesPeople', 'MailingListsPeople']
# from .mlstats_tables import MailingList, MailingListSender, MailingListSenderId, SenderByMailingList, Message, \
#    MessagePeople

from .mlstats_tables import *
