import datetime

from dateutil import parser
from sqlalchemy import Column
from sqlalchemy import Integer, String, BigInteger, DateTime, Boolean
from unidecode import unidecode

from db.setup import Base


class PullRequestCommitFile(Base):
    __tablename__ = 'commit_files'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    slug = Column(String(255), index=True)
    pr_id = Column(BigInteger, nullable=False, index=True)
    commit_sha = Column(String(255), index=True, nullable=False)
    commit_filename = Column(String(255), nullable=False)
    language = Column(Integer, nullable=False)

    def __init__(self,
                 slug,
                 pr_id,
                 commit_sha,
                 commit_filename,
                 language):
        self.slug = slug
        self.pr_id = pr_id
        self.commit_sha = commit_sha
        self.commit_filename = commit_filename
        self.language = language


class PullRequestCommit(Base):
    __tablename__ = 'commits'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    slug = Column(String(255), index=True)
    pr_id = Column(BigInteger, nullable=False, index=True)
    commit_number = Column(Integer, nullable=False)
    commit_sha = Column(String(255), index=True, nullable=False)

    def __init__(self,
                 slug,
                 pr_id,
                 commit_number,
                 commit_sha):
        self.slug = slug
        self.pr_id = pr_id
        self.commit_number = commit_number
        self.commit_sha = commit_sha


class PullRequest(Base):
    __tablename__ = 'pull_requests'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    slug = Column(String(255), index=True)
    issue_id = Column(BigInteger, index=True)  # a pr is a special issue in GitHub
    pr_id = Column(BigInteger, index=True)
    pr_number = Column(Integer)  # duplicate, should be dropped at some point
    # ALTER TABLE pull_requests DROP COLUMN pr_number;
    state = Column(String(20))
    created_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))
    merged_at = Column(DateTime(timezone=True))
    created_by_login = Column(String(255))
    closed_by_login = Column(String(255))
    merged_by_login = Column(String(255))
    assignee_login = Column(String(255))
    title = Column(String(1024))
    num_comments = Column(Integer)
    num_review_comments = Column(Integer)
    num_commits = Column(Integer)
    num_additions = Column(Integer)
    num_deletions = Column(Integer)
    num_changed_files = Column(Integer)
    labels = Column(String(1024))
    pr_num = Column(Integer, nullable=False)
    merged = Column(Boolean)
    merge_sha = Column(String(255))
    html_url = Column(String(255))

    def __init__(self,
                 slug,
                 issue_id,
                 pr_id,
                 pr_num,
                 state,
                 merged,
                 created_at,
                 merged_at,
                 closed_at,
                 created_by_login,
                 merged_by_login,
                 closed_by_login,
                 assignee_login,
                 title,
                 num_comments,
                 num_review_comments,
                 labels,
                 num_commits,
                 num_changed_files,
                 num_additions,
                 num_deletions,
                 merge_sha,
                 html_url):
        self.slug = slug
        self.issue_id = issue_id
        self.pr_id = pr_id
        #self.pr_number = pr_num
        self.state = state
        self.merged = merged

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

        if merged_at is not None and merged_at != 'None':
            st = parser.parse(merged_at)
            self.merged_at = datetime.datetime(st.year, st.month, st.day, st.hour, st.minute, st.second)
        else:
            self.merged_at = None

        self.created_by_login = created_by_login
        self.closed_by_login = closed_by_login
        self.merged_by_login = merged_by_login
        self.assignee_login = assignee_login
        self.title = unidecode(title[:1024]).strip()
        self.num_comments = num_comments
        self.num_review_comments = num_review_comments
        self.num_commits = num_commits
        self.num_additions = num_additions
        self.num_deletions = num_deletions
        self.num_changed_files = num_changed_files
        self.labels = labels
        self.pr_num = pr_num

        self.merge_sha = merge_sha
        self.html_url = html_url

    def __repr__(self):
        return 'pull request (%s): %s' % (self.pr_id, self.title)

# class Comment(Base):
#     __tablename__ = 'comments'
#     __table_args__ = {'extend_existing': True}
#
#     comment_id = Column(BigInteger, primary_key=True)
#     issue_id = Column(BigInteger, nullable=False)
#     issue_number = Column(Integer)
#     slug = Column(String(255))
#     created_at = Column(DateTime(timezone=True))
#     updated_at = Column(DateTime(timezone=True))
#     user_github_id = Column(BigInteger)
#     user_login = Column(String(255))
#     body = Column(LONGTEXT)
#
#     def __init__(self,
#                  comment_id,
#                  slug,
#                  issue_id,
#                  issue_number,
#                  created_at,
#                  updated_at,
#                  user_github_id,
#                  user_login,
#                  body):
#         self.comment_id = int(comment_id)
#         self.issue_id = int(issue_id)
#         self.issue_number = int(issue_number)
#         self.slug = slug
#         self.user_github_id = user_github_id
#         self.user_login = user_login
#         self.body = body
#         if created_at is not None and created_at != 'None':
#             st = parser.parse(created_at)
#             self.created_at = datetime.datetime(st.year, st.month, st.day, st.hour, st.minute, st.second)
#         else:
#             self.created_at = None
#         if updated_at is not None and updated_at != 'None':
#             st = parser.parse(updated_at)
#             self.updated_at = datetime.datetime(st.year, st.month, st.day, st.hour, st.minute, st.second)
#         else:
#             self.updated_at = None
