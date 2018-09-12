import pickle

from apache_projects.orm.apache_tables import *
from commit_analyzer.orm.commit_tables import *
from db.setup import SessionWrapper
from history_analyzer.orm import CommitHistoryDevProject
from logger import logging_config
from ml_downloader.orm.mlstats_tables import *
from unmasking.unmask_aliases import EMAILERS_OFFSET


def main():
    # for each ASF project with a git mirror cloned locally
    projects = sorted(
        session.query(ApacheProject.id, Commit.repo_id, ApacheProject.name, ApacheProject.dev_ml_url,
                      ApacheProject.user_ml_url).filter(
            ApacheProject.name == GithubRepository.slug, GithubRepository.id == Commit.repo_id).distinct().all())
    for p in projects:
        # and with email archives downloaded
        mls = session.query(MailingLists.mailing_list_name).filter(MailingLists.mailing_list_name.ilike('%{0}%'.format(p.name))).all()
        logger.info('Starting the analysis of project %s' % p.name)
        #for ml in mls:
        if mls:
            # all distinct commit authors for current project
            project_authors = session.query(Commit.author_id).filter(Commit.repo_id == GithubRepository.id,
                                                                     GithubRepository.slug == p.name).distinct().all()
            # all distinct commit integrators for current project and the timestamp of the first integration
            project_committers = session.query(Commit.committer_id, Commit.timestamp_utc).filter(
                Commit.repo_id == GithubRepository.id,
                GithubRepository.slug == p.name).order_by(Commit.committer_id, Commit.timestamp_utc).all()

            for c_author in project_authors:
                # TODO we will take care of alias unmasking and merging during CSV export
                commits_authored_while_not_a_committer = list()
                author_commits = session.query(Commit, GithubDeveloper.user_id, GithubDeveloper.name,
                                               GithubDeveloper.email).filter(
                    # filter commits from local git repo authored by current author
                    Commit.author_id == c_author.author_id,
                    Commit.author_id == GithubDeveloper.user_id,
                    # filter project commits
                    Commit.repo_id == p.repo_id,
                    GithubDeveloper.repo_id == p.repo_id,
                    # exclude self-merged
                    Commit.author_id != Commit.committer_id,
                ).order_by(Commit.timestamp_utc).distinct().all()

                for ac in author_commits:
                    if not was_committer_at_date(c_author.author_id, ac.Commit.timestamp_utc, project_committers):
                        commits_authored_while_not_a_committer.append(ac.Commit)
                        logger.debug(
                            '[project {0}, author {1}] appended commit {2}'.format(p.name, c_author.author_id,
                                                                                   ac.Commit.sha))

                # TODO filter email threshold in R
                n_author_commits = len(commits_authored_while_not_a_committer)
                len_author_track_record = 0
                authored_commit_shas = None
                first_authored_sha = None
                first_authored_datetime = None
                last_authored_sha = None
                last_authored_datetime = None
                tot_num_additions_authored = 0
                tot_num_deletions_authored = 0
                tot_num_files_changed_authored = 0
                tot_src_loc_added_authored = 0
                tot_src_loc_deleted_authored = 0
                tot_src_files_touched_authored = 0
                if n_author_commits > 0:
                    first = commits_authored_while_not_a_committer[0]
                    first_authored_sha = first.sha
                    first_authored_datetime = first.timestamp_utc

                    last = commits_authored_while_not_a_committer[n_author_commits - 1]
                    last_authored_sha = last.sha
                    last_authored_datetime = last.timestamp_utc
                    len_author_track_record = (last_authored_datetime - first_authored_datetime).days

                    authored_commit_shas = list()
                    for c in commits_authored_while_not_a_committer:
                        authored_commit_shas.append(c.sha)
                        tot_num_additions_authored += c.num_additions
                        tot_num_deletions_authored += c.num_deletions
                        tot_num_files_changed_authored += c.num_files_changed
                        tot_src_loc_added_authored += c.src_loc_added
                        tot_src_loc_deleted_authored += c.src_loc_deleted
                        tot_src_files_touched_authored += c.num_src_files_touched

                    authored_commit_shas = ','.join(authored_commit_shas)

                integrated_commit_shas = list()
                n_integrated_commits = 0
                len_integrator_track_record = 0
                first_integrated_sha = None
                first_integrated_datetime = None
                last_integrated_sha = None
                last_integrated_datetime = None
                tot_num_additions_integrated = 0
                tot_num_deletions_integrated = 0
                tot_num_files_changed_integrated = 0
                tot_src_loc_added_integrated = 0
                tot_src_loc_deleted_integrated = 0
                tot_src_files_touched_integrated = 0
                if is_also_committer(c_author.author_id, project_committers):
                    integrator_commits = session.query(Commit).filter(
                        # filter commits from local git repo authored by current author
                        Commit.committer_id == c_author.author_id,
                        Commit.committer_id == GithubDeveloper.user_id,
                        # filter project commits
                        Commit.repo_id == p.repo_id,
                        GithubDeveloper.repo_id == p.repo_id,
                        # exclude self-merged
                        Commit.author_id != Commit.committer_id,
                    ).order_by(Commit.timestamp_utc).distinct().all()

                    n_integrated_commits = len(integrator_commits)
                    if n_integrated_commits > 0:
                        first = integrator_commits[0]
                        first_integrated_sha = first.sha
                        first_integrated_datetime = first.timestamp_utc
                        last = integrator_commits[n_integrated_commits - 1]
                        last_integrated_sha = last.sha
                        last_integrated_datetime = last.timestamp_utc
                        len_integrator_track_record = (last_integrated_datetime - first_integrated_datetime).days

                        for c in integrator_commits:
                            integrated_commit_shas.append(c.sha)
                            tot_num_additions_integrated += c.num_additions
                            tot_num_deletions_integrated += c.num_deletions
                            tot_num_files_changed_integrated = c.num_files_changed
                            tot_src_loc_added_integrated += c.src_loc_added
                            tot_src_loc_deleted_integrated += c.src_loc_deleted
                            tot_src_files_touched_integrated += c.num_src_files_touched

                integrated_commit_shas = ','.join(integrated_commit_shas)
                try:
                    entry = CommitHistoryDevProject(dev_uid=c_author.author_id,
                                                    project_name=p.name,
                                                    num_authored_commits=n_author_commits,
                                                    num_integrated_commits=n_integrated_commits,
                                                    author_track_record_days=len_author_track_record,
                                                    committer_track_record_days=len_integrator_track_record,
                                                    authored_commit_shas=authored_commit_shas,
                                                    integrated_commit_shas=integrated_commit_shas,
                                                    first_authored_sha=first_authored_sha,
                                                    first_authored_datetime=first_authored_datetime,
                                                    last_authored_sha=last_authored_sha,
                                                    last_authored_datetime=last_authored_datetime,
                                                    first_integrated_sha=first_integrated_sha,
                                                    first_integrated_datetime=first_integrated_datetime,
                                                    last_integrated_sha=last_integrated_sha,
                                                    last_integrated_datetime=last_integrated_datetime,
                                                    tot_num_additions_authored=tot_num_additions_authored,
                                                    tot_num_deletions_authored=tot_num_deletions_authored,
                                                    tot_num_files_changed_authored=tot_num_files_changed_authored,
                                                    tot_src_loc_added_authored=tot_src_loc_added_authored,
                                                    tot_src_loc_deleted_authored=tot_src_loc_deleted_authored,
                                                    tot_src_files_touched_authored=tot_src_files_touched_authored,
                                                    tot_num_additions_integrated=tot_num_additions_integrated,
                                                    tot_num_deletions_integrated=tot_num_deletions_integrated,
                                                    tot_num_files_changed_integrated=tot_num_files_changed_integrated,
                                                    tot_src_loc_added_integrated=tot_src_loc_added_integrated,
                                                    tot_src_loc_deleted_integrated=tot_src_loc_deleted_integrated,
                                                    tot_src_files_touched_integrated=tot_src_files_touched_integrated)
                    session.add(entry)
                    session.commit()
                    logger.info(
                        msg='Done with author {0} of project {1}, added {2} authored commits'.format(
                            c_author.author_id, p.name, len(commits_authored_while_not_a_committer)))
                except Exception as e:
                    logger.error('Error saving dev project commit', e)
    logger.info('Done with project {0}'.format(p.name))


def is_also_committer(aid, project_committers):
    return aid in set([x.committer_id for x in project_committers])


def was_committer_at_date(aid, timestamp, project_committers):
    was_project_committer = False
    uid = alias_map[aid]
    aliases = get_alias_ids(alias_map, uid) + [uid, ]
    for alias in aliases:
        alias = abs(alias)
        if alias > EMAILERS_OFFSET:
            # mailing list id, ignore
            continue
        # elif alias in project_committers:
        for i in range(0, len(project_committers) - 1):
            if project_committers[i].committer_id == alias:
                if project_committers[i].timestamp_utc <= timestamp:
                    was_project_committer = True
                # commits are ordered by timestamp_utc
                # therefore if the first is larger than the timestamp, so are the next ones and
                # we can safely break and go look for other aliases
                break
    return was_project_committer


def load_alias_map(filename):
    with open(filename, "rb") as f:
        unpickler = pickle.Unpickler(f)
        aliases = unpickler.load()
    return aliases


def get_alias_ids(_map, uid):
    aliases = set()
    for key in _map.keys():
        if _map[key] == uid and key != uid:
            aliases.add(key)
    return list(aliases)


def reset_commit_history_table():
        session.query(CommitHistoryDevProject).delete()
        session.commit()


if __name__ == '__main__':
    logger = logging_config.get_logger('commit_history')
    SessionWrapper.load_config('../db/cfg/setup.yml')
    session = SessionWrapper.new(init=True)
    reset_commit_history_table()

    alias_map = load_alias_map('../unmasking/idm/dict/alias_map.dict')
    try:
        main()
    except KeyboardInterrupt:
        logger.error('Received Ctrl-C or other break signal. Exiting.')
