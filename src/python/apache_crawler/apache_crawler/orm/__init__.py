__all__ = ['setup', 'tables']

from apache_crawler.orm.setup import SessionWrapper
from apache_crawler.orm.tables import ApacheDeveloper, ApacheProject, ProjectCommitter, PmcMember

SessionWrapper.load_config()
SessionWrapper.new(init=True)
