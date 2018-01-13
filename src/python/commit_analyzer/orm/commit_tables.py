from sqlalchemy import Column
from sqlalchemy import Integer, String, BigInteger, DateTime, Text, Index
from sqlalchemy.dialects.mysql import LONGTEXT
from unidecode import unidecode

from db.setup import Base


class GithubRepository(Base):
    __tablename__ = 'local_repositories'

    id = Column(BigInteger, primary_key=True)
    slug = Column(String(255), index=True)
    min_commit = Column(DateTime(timezone=True))
    max_commit = Column(DateTime(timezone=True))
    total_commits = Column(Integer)

    def __init__(self,
                 slug,
                 min_commit,
                 max_commit,
                 total_commits):
        self.slug = slug
        self.min_commit = min_commit
        self.max_commit = max_commit
        self.total_commits = total_commits


class GithubDeveloper(Base):
    __tablename__ = 'local_developers'

    id = Column(BigInteger, primary_key=True)
    repo_id = Column(BigInteger, index=True, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    name = Column(Text)
    email = Column(Text, nullable=False)

    def __init__(self,
                 repo_id,
                 user_id,
                 name,
                 email):
        self.repo_id = repo_id
        self.user_id = user_id
        self.name = unidecode(name[:255]).strip()
        self.email = email


class Commit(Base):
    __tablename__ = 'local_commits'

    id = Column(BigInteger, primary_key=True)
    repo_id = Column(BigInteger, nullable=False)
    sha = Column(String(255), index=True, nullable=False)
    timestamp_utc = Column(DateTime(timezone=True))
    author_id = Column(BigInteger, nullable=False)
    committer_id = Column(BigInteger, nullable=False)
    message = Column(LONGTEXT)
    num_parents = Column(Integer)
    num_additions = Column(Integer)
    num_deletions = Column(Integer)
    num_files_changed = Column(Integer)
    files = Column(LONGTEXT)  # comma-separated list of file names
    src_loc_added = Column(Integer)
    src_loc_deleted = Column(Integer)
    num_src_files_touched = Column(Integer)
    src_files = Column(LONGTEXT)  # comma-separated list of file names

    def __init__(self,
                 repo_id,
                 sha,
                 timestamp_utc,
                 author_id,
                 committer_id,
                 message,
                 num_parents,
                 num_additions,
                 num_deletions,
                 num_files_changed,
                 files,
                 src_loc_added,
                 src_loc_deleted,
                 num_src_files_touched,
                 src_files
                 ):
        self.repo_id = repo_id
        self.sha = sha
        self.timestamp_utc = timestamp_utc
        self.author_id = author_id
        self.committer_id = committer_id
        self.message = unidecode(message[:len(message)]).strip()
        self.num_parents = num_parents
        self.num_additions = num_additions
        self.num_deletions = num_deletions
        self.num_files_changed = num_files_changed
        self.src_loc_added = src_loc_added
        self.src_loc_deleted = src_loc_deleted
        self.num_src_files_touched = num_src_files_touched
        self.src_files = src_files
        self.files = files


class CommitFiles(Base):
    __tablename__ = 'local_commit_files'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    repo_id = Column(BigInteger, index=True, nullable=False)
    repo_slug = Column(String(255), nullable=False)
    commit_sha = Column(String(255), nullable=False)
    file = Column(String(255), nullable=False)
    loc_added = Column(Integer)
    loc_deleted = Column(Integer)
    language = Column(Integer)

    __table_args__ = (Index('ix_commitfiles', "commit_sha", "repo_slug", "file", unique=True),)

    def __init__(self,
                 repo_id,
                 repo_slug,
                 commit_sha,
                 _file,
                 loc_add,
                 loc_del,
                 lang
                 ):
        self.repo_id = repo_id
        self.repo_slug = repo_slug
        self.commit_sha = commit_sha
        self.file = _file
        self.loc_added = loc_add
        self.loc_deleted = loc_del
        self.language = lang
