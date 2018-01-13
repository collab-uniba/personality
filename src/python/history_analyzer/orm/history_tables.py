from sqlalchemy import Column
from sqlalchemy import Integer, BigInteger, String, TEXT, DateTime

from db.setup import Base


class CommitHistoryDevProject(Base):
    __tablename__ = 'commit_history'

    dev_uid = Column(BigInteger, primary_key=True)
    project_name = Column(String(255), primary_key=True)

    num_authored_commits = Column(Integer)
    num_integrated_commits = Column(Integer)

    author_track_record_days = Column(Integer)  # no of days
    committer_track_record_days = Column(Integer)

    authored_commit_shas = Column(TEXT)  # comma-separated string list
    integrated_commit_shas = Column(TEXT)

    first_authored_sha = Column(String(255))
    first_authored_datetime = Column(DateTime)
    last_authored_sha = Column(String(255))
    last_authored_datetime = Column(DateTime)

    first_integrated_sha = Column(String(255))
    first_integrated_datetime = Column(DateTime)
    last_integrated_sha = Column(String(255))
    last_integrated_datetime = Column(DateTime)

    tot_num_additions_authored = Column(Integer)
    tot_num_deletions_authored = Column(Integer)
    tot_num_files_changed_authored = Column(Integer)
    tot_src_loc_added_authored = Column(Integer)
    tot_src_loc_deleted_authored = Column(Integer)
    tot_src_files_touched_authored = Column(Integer)

    tot_num_additions_integrated = Column(Integer)
    tot_num_deletions_integrated = Column(Integer)
    tot_num_files_changed_integrated = Column(Integer)
    tot_src_loc_added_integrated = Column(Integer)
    tot_src_loc_deleted_integrated = Column(Integer)
    tot_src_files_touched_integrated = Column(Integer)

    def __init__(self,
                 dev_uid,
                 project_name,
                 num_authored_commits,
                 num_integrated_commits,
                 author_track_record_days,
                 committer_track_record_days,
                 authored_commit_shas,
                 integrated_commit_shas,
                 first_authored_sha,
                 first_authored_datetime,
                 last_authored_sha,
                 last_authored_datetime,
                 first_integrated_sha,
                 first_integrated_datetime,
                 last_integrated_sha,
                 last_integrated_datetime,
                 tot_num_additions_authored,
                 tot_num_deletions_authored,
                 tot_num_files_changed_authored,
                 tot_src_loc_added_authored,
                 tot_src_loc_deleted_authored,
                 tot_src_files_touched_authored,
                 tot_num_additions_integrated,
                 tot_num_deletions_integrated,
                 tot_num_files_changed_integrated,
                 tot_src_loc_added_integrated,
                 tot_src_loc_deleted_integrated,
                 tot_src_files_touched_integrated
                 ):
        self.dev_uid = dev_uid
        self.project_name = project_name

        self.num_authored_commits = num_authored_commits
        self.num_integrated_commits = num_integrated_commits

        self.author_track_record_days = author_track_record_days
        self.committer_track_record_days = committer_track_record_days

        self.authored_commit_shas = authored_commit_shas
        self.integrated_commit_shas = integrated_commit_shas

        self.first_authored_sha = first_authored_sha
        self.first_authored_datetime = first_authored_datetime
        self.last_authored_sha = last_authored_sha
        self.last_authored_datetime = last_authored_datetime

        self.first_integrated_sha = first_integrated_sha
        self.first_integrated_datetime = first_integrated_datetime
        self.last_integrated_sha = last_integrated_sha
        self.last_integrated_datetime = last_integrated_datetime

        self.tot_num_additions_authored = tot_num_additions_authored
        self.tot_num_deletions_authored = tot_num_deletions_authored
        self.tot_num_files_changed_authored = tot_num_files_changed_authored
        self.tot_src_loc_added_authored = tot_src_loc_added_authored
        self.tot_src_loc_deleted_authored = tot_src_loc_deleted_authored
        self.tot_src_files_touched_authored = tot_src_files_touched_authored

        self.tot_num_additions_integrated = tot_num_additions_integrated
        self.tot_num_deletions_integrated = tot_num_deletions_integrated
        self.tot_num_files_changed_integrated = tot_num_files_changed_integrated
        self.tot_src_loc_added_integrated = tot_src_loc_added_integrated
        self.tot_src_loc_deleted_integrated = tot_src_loc_deleted_integrated
        self.tot_src_files_touched_integrated = tot_src_files_touched_integrated
