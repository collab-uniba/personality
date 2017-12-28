import datetime

from dateutil import parser
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import String

from db.setup import Base


class MailingList(Base):
    __tablename__ = 'mailing_lists'

    mailing_list_url = Column(String(255), primary_key=True)
    mailing_list_name = Column(String(255))
    project_name = Column(String(255))
    last_analysis = Column(DateTime)

    def __init__(self,
                 mailing_list_url,
                 mailing_list_name,
                 project_name,
                 last_analysis,
                 ):
        self.mailing_list_url = mailing_list_url
        self.mailing_list_name = mailing_list_name
        self.project_name = project_name
        if last_analysis is not None and last_analysis != 'None':
            st = parser.parse(last_analysis)
            self.last_analysis = datetime.datetime(st.year, st.month, st.day, st.hour, st.minute, st.second)
        else:
            self.last_analysis = None
