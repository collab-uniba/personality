import itertools
import logging
import os
import sys
import traceback
from _datetime import datetime
from datetime import timedelta, timezone

import pygit2
from sqlalchemy import and_, func
from sqlalchemy.orm import exc

from commit_analyzer.orm import *
from db.setup import SessionWrapper
from pr_downloader.activity_classifier import BasicFileTypeClassifier
from logger import logging_config

def parse_commits(slug, repos_folder):
    contributors = {}
    counter = itertools.count(start=1)
    basic_classifier = BasicFileTypeClassifier()

    session = SessionWrapper.new()

    logger.info('Parsing commits, commit files, and developers from project %s' % slug)
    try:
        folder_path = os.path.abspath(os.path.join(repos_folder, slug))

        min_commit = datetime.now(timezone.utc)
        max_commit = min_commit - timedelta(days=100 * 365)
        total_commits = 0

        if not os.path.exists(folder_path):
            return slug

        try:
            db_repo = session.query(GithubRepository).filter_by(slug=slug).one()
            if db_repo.total_commits == 0:
                # first delete the empty row, likely produced by an interrupted execution
                # then raise exception to attempt a new parsing
                try:
                    session.delete(db_repo)
                    session.commit()
                except:
                    logger.error('Error trying to delete empty row for repository %s' % slug)
                    return
                raise exc.NoResultFound
            else:
                # the reason why we return here is to skip analyzing
                # again a repo in case of crashing exception that forces
                # the script to be run again
                logger.debug('Project %s seems to have been already processed, skipping' % slug)
                return slug
        except exc.NoResultFound:
            db_repo = GithubRepository(slug,
                                       min_commit,
                                       max_commit,
                                       total_commits)
            session.add(db_repo)
            session.commit()
        except exc.MultipleResultsFound:
            logger.warning(msg="Found multiple results querying for repo %s." % slug)
            pass

        git_repo = pygit2.Repository(folder_path)

        last = git_repo[git_repo.head.target]

        # Fetch all commits as an iterator, and iterate it
        for c in git_repo.walk(last.id, pygit2.GIT_SORT_TIME):
            commit = CommitWrapper(c)

            total_commits += 1

            sha = commit.get_sha()

            authored_datetime = commit.get_authored_date()
            committed_datetime = commit.get_committed_date()

            if authored_datetime < min_commit:
                min_commit = authored_datetime
            if authored_datetime > max_commit:
                max_commit = authored_datetime

            (author_name, author_email) = commit.get_author()
            (author_name_l, author_email_l) = (author_name.lower(), author_email.lower())
            (committer_name, committer_email) = commit.get_committer()
            (committer_name_l, committer_email_l) = (committer_name.lower(), committer_email.lower())

            if (author_name_l, author_email_l) not in contributors:
                contributors[(author_name_l, author_email_l)] = next(counter)
            author_id = contributors[(author_name_l, author_email_l)]

            if (committer_name_l, committer_email_l) not in contributors:
                contributors[(committer_name_l, committer_email_l)] = next(counter)
            committer_id = contributors[(committer_name_l, committer_email_l)]

            parents = commit.get_parents()
            num_parents = len(parents)
            if not num_parents:
                continue

            message = commit.get_message().strip()

            try:
                db_commit = session.query(Commit).filter_by(sha=sha).one()
                continue  # if already present, stop and go on analyzing the next one
            except exc.NoResultFound:
                diff = commit.get_diff(git_repo)
                loc_added = diff.stats.insertions
                loc_deleted = diff.stats.deletions
                num_files_touched = diff.stats.files_changed

                # get info about changes to src files in the new  commit
                all_files, src_files, num_src_files_touched, src_loc_added, src_loc_deleted = \
                    CommitWrapper.get_src_changes(basic_classifier, diff)

                db_commit = Commit(db_repo.id,
                                   sha,
                                   authored_datetime,
                                   author_id,
                                   committer_id,
                                   message,
                                   num_parents,
                                   loc_added,
                                   loc_deleted,
                                   num_files_touched,
                                   all_files,
                                   src_loc_added,
                                   src_loc_deleted,
                                   num_src_files_touched,
                                   src_files)
                session.add(db_commit)
                # required to flush the pending data before adding to the CommitFiles table below
                session.commit()

                # parse changed files per diff
                for patch in diff:
                    commit_file = os.path.basename(patch.delta.new_file.path)
                    try:
                        commit_file = session.query(CommitFiles).filter_by(commit_sha=sha, repo_slug=slug,
                                                                           file=commit_file).one()
                        continue  # if already present, stop and go on analyzing the next one
                    except exc.NoResultFound:
                        lang = basic_classifier.label_file(commit_file)
                        loc_ins = 0
                        loc_del = 0
                        for hunk in patch.hunks:
                            for hl in hunk.lines:
                                if hl.origin == '-':
                                    loc_del -= 1
                                elif hl.origin == '+':
                                    loc_ins += 1
                        commit_file = CommitFiles(db_repo.id, db_repo.slug, sha, commit_file, loc_ins, loc_del, lang)
                        session.add(commit_file)

                session.commit()

        for (name, email), user_id in sorted(contributors.items(), key=lambda e: e[1]):
            try:
                db_user = session.query(GithubDeveloper).filter(and_(GithubDeveloper.name == func.binary(name),
                                                                     GithubDeveloper.email == func.binary(email),
                                                                     GithubDeveloper.repo_id == db_repo.id)).one()
            except exc.NoResultFound:
                db_user = GithubDeveloper(db_repo.id, user_id, name, email)
                session.add(db_user)
            except exc.MultipleResultsFound:
                # Would this happens because we allow name aliases during mining?
                # Should we deal with it? And how?
                logger.warning(
                    msg="Multiple entries for user \'{0}\' <{1}> in repo {2}".format(name, email, db_repo.slug))

        db_repo.min_commit = min_commit
        db_repo.max_commit = max_commit
        db_repo.total_commits = total_commits
        session.add(db_repo)

        session.commit()
        logger.info('Done')
        return slug

    except Exception as e:
        logger.error(msg="{0}: unknown error:\t{1}".format(slug, e))
        traceback.print_exc()
    finally:
        return slug


if __name__ == '__main__':
    logging.basicConfig()
    logger = logging_config.get_logger('commit_analyzer', logging.DEBUG)

    # create a new session and init db tables
    SessionWrapper.load_config('../db/cfg/setup.yml')
    SessionWrapper.new(init=True)

    repos = [d for d in os.listdir(os.path.abspath(sys.argv[1]))]

    for r in repos:
        parse_commits(r, repos_folder=sys.argv[1])
