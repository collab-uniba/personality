from sqlalchemy import String, Column
from sqlalchemy.dialects.mysql import LONGTEXT

from db.setup import Base


class UsersLocation(Base):
    __tablename__ = 'users_location'
    __table_args__ = {
        'extend_existing': True,
        'mysql_row_format': 'DYNAMIC'
    }

    username = Column(String(255), primary_key=True)
    location = Column(String(255))
    bio = Column(String(255, collation='utf8mb4_unicode_ci'))
    company = Column(String(255))

    def __init__(self, username, location, bio, company):
        self.username = username
        self.location = location
        self.bio = bio
        self.company = company
