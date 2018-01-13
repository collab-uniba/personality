from sqlalchemy import Column, String, BigInteger, Integer
from sqlalchemy.dialects.mysql import JSON

from db.setup import Base


class PersonalityProjectMonth(Base):
    __tablename__ = 'personality'

    dev_uid = Column(BigInteger, primary_key=True)
    project_name = Column(String(255), primary_key=True)
    month = Column(String(8), primary_key=True)
    email_count = Column(Integer)
    word_count = Column(BigInteger)
    scores = Column(JSON)

    def __init__(self,
                 dev_uid,
                 project_name,
                 month,
                 email_count,
                 word_count,
                 scores):
        self.dev_uid = dev_uid
        self.project_name = project_name
        self.month = month
        self.email_count = email_count
        self.word_count = word_count
        self.scores = scores

    def __repr__(self):
        return 'developer id {0} scores, on project {1}, during month {2}'.format(self.uid,
                                                                                  self.project,
                                                                                  self.month)
