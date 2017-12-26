import datetime

from dateutil import parser
from sqlalchemy import Column
from sqlalchemy import Integer, String, BigInteger, DateTime
from sqlalchemy.dialects.mysql import LONGTEXT
from unidecode import unidecode

from db.setup import Base


class PullRequest(Base):
    __tablename__ = 'pull_requests'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    slug = Column(String(255), index=True)
    issue_id = Column(BigInteger, index=True)  # a pr is a special issue in GitHub
    issue_number = Column(Integer)
    state = Column(String(20))
    created_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))
    created_by_login = Column(String(255))
    closed_by_login = Column(String(255))
    assignee_login = Column(String(255))
    title = Column(String(1024))
    num_comments = Column(Integer)
    labels = Column(String(1024))
    pr_num = Column(Integer, nullable=False)

    def __init__(self,
                 slug,
                 issue_id,
                 issue_number,
                 state,
                 created_at,
                 closed_at,
                 created_by_login,
                 closed_by_login,
                 assignee_login,
                 title,
                 num_comments,
                 labels,
                 pr_num):

        self.slug = slug
        self.issue_id = issue_id
        self.issue_number = issue_number
        self.state = state

        if created_at is not None and created_at != 'None':
            st = parser.parse(created_at)
            self.created_at = datetime.datetime(st.year, st.month, st.day, st.hour, st.minute, st.second)
        else:
            self.created_at = None

        if closed_at is not None and closed_at != 'None':
            st = parser.parse(closed_at)
            self.closed_at = datetime.datetime(st.year, st.month, st.day, st.hour, st.minute, st.second)
        else:
            self.closed_at = None

        self.created_by_login = created_by_login
        self.closed_by_login = closed_by_login
        self.assignee_login = assignee_login
        self.title = unidecode(title[:1024]).strip()
        self.num_comments = num_comments
        self.labels = labels
        self.pr_num = pr_num

    def __repr__(self):
        return 'Pull request: %s' % self.title


class Comment(Base):
    __tablename__ = 'comments'
    __table_args__ = {'extend_existing': True}

    comment_id = Column(BigInteger, primary_key=True)
    issue_id = Column(BigInteger, nullable=False)
    issue_number = Column(Integer)
    slug = Column(String(255))
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    user_github_id = Column(BigInteger)
    user_login = Column(String(255))
    body = Column(LONGTEXT)

    def __init__(self,
                 comment_id,
                 slug,
                 issue_id,
                 issue_number,
                 created_at,
                 updated_at,
                 user_github_id,
                 user_login,
                 body):
        self.comment_id = int(comment_id)
        self.issue_id = int(issue_id)
        self.issue_number = int(issue_number)
        self.slug = slug
        self.user_github_id = user_github_id
        self.user_login = user_login
        self.body = body
        if created_at is not None and created_at != 'None':
            st = parser.parse(created_at)
            self.created_at = datetime.datetime(st.year, st.month, st.day, st.hour, st.minute, st.second)
        else:
            self.created_at = None
        if updated_at is not None and updated_at != 'None':
            st = parser.parse(updated_at)
            self.updated_at = datetime.datetime(st.year, st.month, st.day, st.hour, st.minute, st.second)
        else:
            self.updated_at = None
