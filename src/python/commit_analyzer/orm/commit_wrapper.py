import logging
import os
from datetime import datetime, timezone, timedelta

import pytz


class CommitWrapper:
    def __init__(self, commit):
        self.commit = commit

    def get_sha(self):
        return self.commit.hex

    def get_committer(self):
        return self.commit.committer.name, self.commit.committer.email

    def get_author(self):
        return self.commit.author.name, self.commit.author.email

    def get_committed_date(self):
        tzinfo = timezone(timedelta(minutes=self.commit.committer.offset))
        dt = datetime.fromtimestamp(float(self.commit.committer.time), tzinfo).astimezone(pytz.utc)
        return dt

    def get_authored_date(self):
        tzinfo = timezone(timedelta(minutes=self.commit.author.offset))
        dt = datetime.fromtimestamp(float(self.commit.author.time), tzinfo).astimezone(pytz.utc)
        return dt

    def get_message(self):
        return self.commit.message

    def get_parents(self):
        return self.commit.parents

    def get_diff(self, repo):
        return repo.diff(self.commit.parents[0], self.commit, context_lines=0)

    @staticmethod
    def get_src_changes(basic_classifier, diff):
        src_loc_added = 0
        src_loc_deleted = 0
        num_src_files_touched = 0
        src_files = []
        all_files = []
        for patch in diff:
            if not patch.delta.is_binary:
                """
                unlike the blame part, here we look at the new files of the patch
                as they contain both the old files that are being modified, plus
                the new ones, just created from scratch
                """
                f = patch.delta.new_file
                all_files.append(os.path.basename(f.path))
                if basic_classifier.label_file(f.path) != basic_classifier.DOC:  # not a doc file
                    num_src_files_touched += 1
                    src_files.append(os.path.basename(f.path))
                    for hunk in patch.hunks:
                        for hl in hunk.lines:
                            if hl.origin == '-':
                                src_loc_deleted += 1
                            elif hl.origin == '+':
                                src_loc_added += 1
                else:
                    logging.debug("Skipped doc file %s" % f.path)
            else:
                logging.debug("Skipped binary delta.")
        if src_files:
            src_files = ','.join(src_files)
        else:
            src_files = ''
        if all_files:
            all_files = ','.join(all_files)
        else:
            all_files = ''
        return all_files, src_files, num_src_files_touched, src_loc_added, src_loc_deleted
