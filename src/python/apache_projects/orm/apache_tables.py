from sqlalchemy import BigInteger
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from db.setup import Base


class ApacheDeveloper(Base):
    __tablename__ = 'developers'

    id = Column(BigInteger, primary_key=True)
    login = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)

    def __init__(self,
                 name,
                 login
                 ):
        self.name = name
        self.login = login


class ApacheProject(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    status = Column(String(24))
    category = Column(String(32))
    language = Column(String(24))
    pmc_chair = Column(String(255))  # , ForeignKey("developers.name") ApacheDeveloper
    url = Column(String(255))
    repository_url = Column(String(255), nullable=False)
    repository_type = Column(String(10), nullable=False)
    bug_tracker_url = Column(String(255))
    dev_ml_url = Column(String(255), nullable=False)
    user_ml_url = Column(String(255), nullable=False)

    def __init__(self,
                 name,
                 status,
                 category,
                 language,
                 pmc_chair,
                 url,
                 repository_url,
                 repository_type,
                 bug_tracker_url,
                 dev_ml_url,
                 user_ml_url):
        self.name = name
        self.status = status
        self.category = category
        self.language = language
        self.pmc_chair = pmc_chair
        self.url = url
        self.repository_url = repository_url
        self.repository_type = repository_type
        self.bug_tracker_url = bug_tracker_url
        self.dev_ml_url = dev_ml_url
        self.user_ml_url = user_ml_url


class ProjectCommitter(Base):
    __tablename__ = 'project_committers'

    project_id = Column(Integer, primary_key=True)
    developer_id = Column(BigInteger, primary_key=True)

    def __init__(self,
                 project_id,
                 developer_id
                 ):
        self.project_id = project_id
        self.developer_id = developer_id


class PmcMember(Base):
    __tablename__ = 'pmc_members'

    project_id = Column(Integer, primary_key=True)
    developer_id = Column(BigInteger, primary_key=True)

    def __init__(self,
                 project_id,
                 developer_id
                 ):
        self.project_id = project_id
        self.developer_id = developer_id
