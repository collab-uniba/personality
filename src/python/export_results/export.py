import json
import logging

from dateutil.relativedelta import relativedelta

from apache_projects.orm import ApacheProject
from commit_analyzer.orm import GithubRepository
from commons.aliasing import load_alias_map
from commons.csv_utils import CsvWriter
from db import SessionWrapper
from history_analyzer.orm import CommitHistoryDevProject
from logger import logging_config
from personality_insights.orm import PersonalityProjectMonth


def merge_result_by_alias(res):
    # uids are already unaliased
    uids_prjs = set(sorted((_r['uid'], _r['project']) for _r in res))
    new_dicts = list()
    for uid, prj in uids_prjs:
        sel = [_r for _r in res if _r['uid'] == uid and _r['project'] == prj]

        if sel:
            new_dict = dict()
            new_dicts.append(new_dict)
            new_dict['uid'] = uid
            new_dict['project'] = prj
            new_dict['project_status'] = sel[0]['project_status']
            new_dict['project_language'] = sel[0]['project_language']
            new_dict['project_category'] = sel[0]['project_category']
            new_dict['project_size'] = sel[0]['project_size']
            new_dict['project_age'] = sel[0]['project_age']

            new_dict['author_track_record_days'] = 0
            new_dict['num_authored_commits'] = 0
            new_dict['num_integrated_commits'] = 0
            new_dict['integrator_track_record_days'] = 0
            new_dict['first_authored_datetime'] = None
            new_dict['last_authored_datetime'] = None
            new_dict['first_integrated_datetime'] = None
            new_dict['last_integrated_datetime'] = None
            new_dict['tot_num_additions_authored'] = 0
            new_dict['tot_num_deletions_authored'] = 0
            new_dict['tot_num_files_changed_authored'] = 0
            new_dict['tot_src_loc_added_authored'] = 0
            new_dict['tot_src_loc_deleted_authored'] = 0
            new_dict['tot_src_files_touched_authored'] = 0

            new_dict['tot_num_additions_integrated'] = 0
            new_dict['tot_num_deletions_integrated'] = 0
            new_dict['tot_num_files_changed_integrated'] = 0
            new_dict['tot_src_loc_added_integrated'] = 0
            new_dict['tot_src_loc_deleted_integrated'] = 0
            new_dict['tot_src_files_touched_integrated'] = 0

            new_dict['is_author'] = False
            new_dict['is_integrator'] = False

            for s in sel:
                new_dict['author_track_record_days'] += s['author_track_record_days']
                new_dict['num_authored_commits'] += s['num_authored_commits']
                new_dict['num_integrated_commits'] += s['num_integrated_commits']
                new_dict['integrator_track_record_days'] += s['integrator_track_record_days']
                if s['first_authored_datetime'] and new_dict['first_authored_datetime']:
                    new_dict['first_authored_datetime'] = min(new_dict['first_authored_datetime'],
                                                              s['first_authored_datetime'])
                else:
                    new_dict['first_authored_datetime'] = s['first_authored_datetime']
                if new_dict['last_authored_datetime'] and s['last_authored_datetime']:
                    new_dict['last_authored_datetime'] = max(new_dict['last_authored_datetime'],
                                                             s['last_authored_datetime'])
                else:
                    new_dict['last_authored_datetime'] = s['last_authored_datetime']
                if new_dict['first_integrated_datetime'] and s['first_integrated_datetime']:
                    new_dict['first_integrated_datetime'] = min(new_dict['first_integrated_datetime'],
                                                                s['first_integrated_datetime'])
                else:
                    new_dict['first_integrated_datetime'] = s['first_integrated_datetime']
                if new_dict['last_integrated_datetime'] and s['last_integrated_datetime']:
                    new_dict['last_integrated_datetime'] = max(new_dict['last_integrated_datetime'],
                                                               s['last_integrated_datetime'])
                else:
                    new_dict['last_integrated_datetime'] = s['last_integrated_datetime']

                new_dict['tot_num_additions_authored'] += s['tot_num_additions_authored']
                new_dict['tot_num_deletions_authored'] += s['tot_num_deletions_authored']
                new_dict['tot_num_files_changed_authored'] += s['tot_num_files_changed_authored']
                new_dict['tot_src_loc_added_authored'] += s['tot_src_loc_added_authored']
                new_dict['tot_src_loc_deleted_authored'] += s['tot_src_loc_deleted_authored']
                new_dict['tot_src_files_touched_authored'] += s['tot_src_files_touched_authored']

                new_dict['tot_num_additions_integrated'] += s['tot_num_additions_integrated']
                new_dict['tot_num_deletions_integrated'] += s['tot_num_deletions_integrated']
                new_dict['tot_num_files_changed_integrated'] += s['tot_num_files_changed_integrated']
                new_dict['tot_src_loc_added_integrated'] += s['tot_src_loc_added_integrated']
                new_dict['tot_src_loc_deleted_integrated'] += s['tot_src_loc_deleted_integrated']
                new_dict['tot_src_files_touched_integrated'] += s['tot_src_files_touched_integrated']

                new_dict['is_author'] = new_dict['is_author'] or s['is_author']
                new_dict['is_integrator'] = new_dict['is_integrator'] or s['is_integrator']

    return new_dicts


def save_personality_results():
    global rows, r, r_dict
    personality_filename = 'personality.csv'
    logger.info('Exporting personality data to file %s' % personality_filename)
    personality_header = ['uid', 'project', 'month', 'email_count', 'word_count',
                          'opennes', 'agreeableness', 'neuroticism', 'extraversion', 'conscientiousness',
                          'opennes_percentile', 'agreeableness_percentile', 'neuroticism_percentile',
                          'extraversion_percentile', 'conscientiousness_percentile']
    personality_writer = CsvWriter(personality_filename, personality_header, 'w')
    rows = session.query(PersonalityProjectMonth).order_by(PersonalityProjectMonth.dev_uid,
                                                           PersonalityProjectMonth.project_name,
                                                           PersonalityProjectMonth.month,
                                                           PersonalityProjectMonth.word_count).all()
    if rows:
        for r in rows:
            r_dict = dict()
            r_dict['uid'] = r.dev_uid
            r_dict['project'] = r.project_name
            r_dict['month'] = r.month
            r_dict['email_count'] = r.email_count
            r_dict['word_count'] = r.word_count
            try:
                scores = json.loads(r.scores.replace('\'', '"').replace('True', '"True"'))
            except json.decoder.JSONDecodeError:
                logger.debug('Empty month % s for developer %s on project %s' % (r.month, r.dev_uid, r.project_name))
                continue
            r_dict['opennes'] = scores["personality"][0]['raw_score']
            r_dict['agreeableness'] = scores["personality"][3]['raw_score']
            r_dict['neuroticism'] = scores["personality"][4]['raw_score']
            r_dict['extraversion'] = scores["personality"][2]['raw_score']
            r_dict['conscientiousness'] = scores["personality"][1]['raw_score']
            r_dict['opennes_percentile'] = scores["personality"][0]['percentile']
            r_dict['agreeableness_percentile'] = scores["personality"][3]['percentile']
            r_dict['neuroticism_percentile'] = scores["personality"][4]['percentile']
            r_dict['extraversion_percentile'] = scores["personality"][2]['percentile']
            r_dict['conscientiousness_percentile'] = scores["personality"][1]['percentile']
            personality_writer.writerow(r_dict)

    personality_writer.close()
    logger.info('Done')


def save_commit_results():
    global rows, r, r_dict
    commit_filename = 'commit.csv'
    logger.info('Exporting commit data to file %s' % commit_filename)
    commit_header = ['uid', 'project',
                     'project_status', 'project_category', 'project_language',
                     'project_size', 'project_age',
                     'is_author', 'num_authored_commits', 'author_track_record_days', 'first_authored_datetime',
                     'last_authored_datetime', 'tot_num_additions_authored',
                     'tot_num_deletions_authored', 'tot_num_files_changed_authored',
                     'tot_src_loc_added_authored', 'tot_src_loc_deleted_authored',
                     'tot_src_files_touched_authored',
                     'is_integrator', 'num_integrated_commits', 'integrator_track_record_days',
                     'first_integrated_datetime', 'last_integrated_datetime',
                     'tot_num_additions_integrated', 'tot_num_deletions_integrated',
                     'tot_num_files_changed_integrated', 'tot_src_loc_added_integrated',
                     'tot_src_loc_deleted_integrated', 'tot_src_files_touched_integrated']
    commit_writer = CsvWriter(commit_filename, commit_header, 'w')
    rows = session.query(CommitHistoryDevProject).order_by(CommitHistoryDevProject.dev_uid,
                                                           CommitHistoryDevProject.project_name,
                                                           CommitHistoryDevProject.first_authored_datetime).all()
    entry_list = list()
    if rows:
        for r in rows:
            if r.num_authored_commits == 0 and r.num_integrated_commits == 0:
                logger.debug('Skipped %s for project %s, nothing authored or integrated' % (r.dev_uid, r.project_name))
                continue
            r_dict = dict()
            r_dict['uid'] = alias_map[r.dev_uid]
            r_dict['project'] = r.project_name
            res = session.query(ApacheProject.language, ApacheProject.status, ApacheProject.category).filter_by(
                name=r.project_name).one()
            r_dict['project_status'] = res.status
            r_dict['project_category'] = res.category
            r_dict['project_language'] = res.language
            prj = session.query(GithubRepository.total_commits, GithubRepository.max_commit,
                                GithubRepository.min_commit).filter_by(slug=r.project_name).one()
            r_dict['project_size'] = prj.total_commits
            r_dict['project_age'] = relativedelta(prj.max_commit, prj.min_commit).years

            r_dict['is_author'] = r.first_authored_sha is not None
            r_dict['num_authored_commits'] = r.num_authored_commits
            r_dict['author_track_record_days'] = r.author_track_record_days
            r_dict['first_authored_datetime'] = r.first_authored_datetime
            r_dict['last_authored_datetime'] = r.last_authored_datetime
            r_dict['tot_num_additions_authored'] = r.tot_num_additions_authored
            r_dict['tot_num_deletions_authored'] = r.tot_num_deletions_authored
            r_dict['tot_num_files_changed_authored'] = r.tot_num_files_changed_authored
            r_dict['tot_src_loc_added_authored'] = r.tot_src_loc_added_authored
            r_dict['tot_src_loc_deleted_authored'] = r.tot_src_loc_deleted_authored
            r_dict['tot_src_files_touched_authored'] = r.tot_src_files_touched_authored

            r_dict['is_integrator'] = r.first_integrated_sha is not None
            r_dict['num_integrated_commits'] = r.num_integrated_commits
            r_dict['integrator_track_record_days'] = r.committer_track_record_days
            r_dict['first_integrated_datetime'] = r.first_integrated_datetime
            r_dict['last_integrated_datetime'] = r.last_integrated_datetime
            r_dict['tot_num_additions_integrated'] = r.tot_num_additions_integrated
            r_dict['tot_num_deletions_integrated'] = r.tot_num_deletions_integrated
            r_dict['tot_num_files_changed_integrated'] = r.tot_num_files_changed_integrated
            r_dict['tot_src_loc_added_integrated'] = r.tot_src_loc_added_integrated
            r_dict['tot_src_loc_deleted_integrated'] = r.tot_src_loc_deleted_integrated
            r_dict['tot_src_files_touched_integrated'] = r.tot_src_files_touched_integrated

            entry_list.append(r_dict)

    entry_list = merge_result_by_alias(entry_list)
    commit_writer.writerows(entry_list)
    commit_writer.close()
    logger.info('Done')


if __name__ == '__main__':
    logger = logging_config.get_logger('export', console_level=logging.DEBUG)
    SessionWrapper.load_config('../db/cfg/setup.yml')
    session = SessionWrapper.new(init=True)
    alias_map = load_alias_map('../unmasking/idm/dict/alias_map.dict')

    save_personality_results()
    save_commit_results()
