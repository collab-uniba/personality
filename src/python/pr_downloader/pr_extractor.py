import logging
import os
import socket
import sys
import traceback
from multiprocessing import Manager, Pool
from multiprocessing import current_process

from _mysql_exceptions import IntegrityError
from github import Github
from github.GithubException import *

from db import SessionWrapper
from pr_downloader.activity_classifier import BasicFileTypeClassifier
from pr_downloader.csvutils import CsvWriter, CsvReader
from pr_downloader.gh.api_tokens import Tokens
from pr_downloader.gh.extractor import BaseGitHubThreadedExtractor
from pr_downloader.orm.github_tables import PullRequest, PullRequestCommit, PullRequestCommitFile


class PrAndCommentExtractor(BaseGitHubThreadedExtractor):
    @staticmethod
    def parse_pull_request(pid, g, issue):
        metadata = None
        pull_request = issue.pull_request  # IssuePullRequest
        if pull_request is not None:
            pr_html_url = pull_request.html_url
            pr_num = int(pr_html_url.split('/')[-1])
            pr = issue.repository.get_pull(pr_num)

            issue_id = issue.id
            pr_id = pr.id

            state = issue.state
            merged = pr.merged
            created_at = str(pr.created_at)
            closed_at = str(pr.closed_at)
            merged_at = str(pr.merged_at)

            created_by = pr.user
            created_by_login = None
            if created_by is not None:
                created_by_login = created_by.login

            closed_by = issue.closed_by
            closed_by_login = None
            if closed_by is not None:
                closed_by_login = closed_by.login

            merged_by = pr.merged_by
            merged_by_login = None
            if merged_by is not None:
                merged_by_login = merged_by.login

            assignee = pr.assignee
            assignee_login = None
            if assignee is not None:
                assignee_login = assignee.login

            title = pr.title.strip().replace("\n", "").replace("\r", "")
            merge_sha = pr.merge_commit_sha
            html_url = pr.html_url
            num_comments = pr.comments
            num_review_comments = pr.review_comments
            labels = ','.join([l.name for l in issue.labels])

            num_commits = pr.commits
            num_additions = pr.additions
            num_deletions = pr.deletions
            num_changed_files = pr.changed_files

            pr_commits = list()
            for i in pr.get_commits():
                pr_commits.append(i.sha)
            commit_shas = ','.join(pr_commits)

            pr_files = list()
            for i in pr.get_files():
                pr_files.append('{0}_#_{1}'.format(os.path.basename(i.filename), i.sha))
            commit_files = ','.join(pr_files)

            metadata = [issue_id,
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
                        commit_shas,
                        commit_files,
                        html_url]

            PrAndCommentExtractor.wait_if_depleted(pid, g)

        return metadata

    # @staticmethod
    # def parse_pr_comments(pid, g, slug, issue):
    #     pr_review_comments = list()
    #
    #     comments_pglist = issue.get_comments()
    #     for comment in comments_pglist:
    #         comment_id = comment.id
    #         body = comment.body.strip()
    #         created_at = comment.created_at
    #         updated_at = comment.updated_at
    #         user_login = comment.user.login
    #         user_gh_id = comment.user.id
    #         pr_review_comments.append(
    #             [slug, issue.id, issue.number, comment_id, body, created_at, updated_at, user_login, user_gh_id])
    #
    #     if issue.pull_request is not None:  # double-check it is an actual PR
    #         pr = issue.repository.get_pull(issue.number)
    #         comments_pglist = pr.get_review_comments()
    #         for comment in comments_pglist:
    #             comment_id = comment.id
    #             created_at = comment.created_at
    #             updated_at = comment.updated_at
    #             body = comment.body.strip()
    #             user_login = comment.user.login
    #             user_gh_id = comment.user.id
    #             pr_review_comments.append(
    #                 [slug, pr.id, pr.number, comment_id, body, created_at, updated_at, user_login, user_gh_id])
    #
    #     PrAndCommentExtractor.wait_if_depleted(pid, g)
    #     return pr_review_comments

    def fetch_prs_comments(self, slug):
        pid = current_process().pid
        pr_list = list()
        # comments = list()

        if slug in self.seen:
            logging.debug('[pid: {0}] Skipping {1}'.format(pid, slug))
            return slug, pid, None, pr_list, 'Skipped'  # , comments
        else:
            self.seen.add(slug)

        logger.debug('[pid: {0}] Processing {1}'.format(pid, slug))

        try:
            _token = self.tokens_map[pid]
            g = Github(_token)
            # check rate limit before starting
            PrAndCommentExtractor.wait_if_depleted(pid, g)
            logger.debug(msg="[pid: %s] Process not depleted, keep going." % pid)
            repo = g.get_repo(slug)

            if repo:
                for issue in repo.get_issues(state=u'closed'):
                    try:
                        logger.info(
                            msg='[pid: {0}] Fetching closed pull-request {1} from {2}'.format(pid, issue.number,
                                                                                              slug))
                        metadata_pr = PrAndCommentExtractor.parse_pull_request(pid, g, issue)
                        if metadata_pr:
                            pr_list.append(metadata_pr)

                            # TODO for now, no comments or reviews are extracted.
                            # metadata_pr_comments = PrAndCommentExtractor.parse_pr_comments(pid, g, slug, issue)
                            # if metadata_pr_comments:
                            #    comments.append(metadata_pr_comments)
                    except socket.timeout as ste:
                        logger.error("Socket timeout parsing issue %s" % issue, ste)
                    except RateLimitExceededException:
                        PrAndCommentExtractor.wait_if_depleted(pid, g)
                        continue
                    except GithubException as e:
                        traceback.print_exc(e)
                        continue
                for issue in repo.get_issues(state=u'open'):
                    try:
                        logger.info(
                            msg='[pid: {0}] Fetching open pull-request {1} from {2}'.format(pid, issue.number,
                                                                                            slug))
                        metadata = PrAndCommentExtractor.parse_pull_request(pid, g, issue)
                        pr_list.append(metadata)

                        #  TODO for now, no comments or reviews are extracted.
                        # metadata = PrAndCommentExtractor.parse_pr_comments(pid, g, slug, issue)
                        # if metadata:
                        #     comments.append(metadata)
                    except socket.timeout as ste:
                        logger.error("Socket timeout parsing issue %s" % issue, ste)
                        continue
                    except RateLimitExceededException:
                        PrAndCommentExtractor.wait_if_depleted(pid, g)
                        continue
                    except GithubException as e:
                        traceback.print_exc(e)
                        continue
        except BadCredentialsException:
            logger.warning("Repository %s seems to be private (raised 401/403 error)" % slug)
            return slug, pid, None, pr_list, "%s seems to be private" % slug  # , comments
        except UnknownObjectException:
            logger.warning("Repository %s cannot be found (raised 404 error)" % slug)
            return slug, pid, None, pr_list, "%s not found" % slug  # , comments
        except GithubException as ghe:
            logger.warning("Unknown error for repository %s" % slug)
            return slug, pid, None, pr_list, str(ghe).strip().replace("\n", " ").replace("\r", " ")  # , comments
        except Exception as e:
            traceback.print_exc(e)
            return slug, pid, None, pr_list, str(e).strip().replace("\n", " ").replace("\r", " ")  # , comments

        logger.debug((_token, PrAndCommentExtractor.get_rate_limit(g)))
        return slug, pid, _token, pr_list, None  # , comments

    def start(self, projects, issues_f):  # , comments_f):
        output_folder = os.path.abspath('./')
        log_writer = CsvWriter(os.path.join(output_folder, 'error.log'), 'a')

        f = os.path.join(output_folder, issues_f)
        header = ['slug',
                  'issue_id',
                  'pr_id',
                  'pr_num',
                  'state',
                  'merged',
                  'created_at',
                  'merged_at',
                  'closed_at',
                  'created_by_login',
                  'merged_by_login',
                  'closed_by_login',
                  'assignee_login',
                  'title',
                  'num_comments',
                  'num_review_comments',
                  'labels',
                  'num_commits',
                  'num_changed_files',
                  'num_additions',
                  'num_deletions',
                  'sha',
                  'commit_shas',
                  'html_url']
        pr_writer = CsvWriter(f, 'w+')
        pr_writer.writerow(header)
        logger.debug("Opened pull request file %s" % issues_f)
        # header = None
        # f = os.path.join(output_folder, comments_f)
        # if not os.path.exists(f):
        #     header = ['slug', 'issue_id', 'issue_number', 'comment_id', 'body', 'created_at', 'updated_at',
        #               'user_login', 'user_github_id']
        # comment_writer = CsvWriter(f, 'w')
        # if header:
        #     comment_writer.writerow(header)
        # logger.debug("Opened pr comments file %s" % comments_f)

        self.initialize()
        pool = Pool(processes=self.tokens.length(), initializer=self.initialize, initargs=())
        # pool = Pool(processes=1, initializer=self.initialize, initargs=())
        # projects = ["apache/johnzon", "apache/roller"]

        for result in pool.imap_unordered(self.fetch_prs_comments, projects):
            (slug, pid, _token, pull_requests, error) = result  # , comments_list
            if error is not None:
                logging.error(msg=[slug, error])
                log_writer.writerow([slug, error])
            # elif comments_list:
            else:
                logger.info("Saving pull requests to temp file")
                for pr in pull_requests:
                    if pr is not None:
                        logger.debug(msg="Adding pull request {0} {1}".format([slug], pr))
                        pr_writer.writerow([slug] + pr)
                # logger.info("Saving comments to temp file")
                # for comments in comments_list:
                #     for comment in comments:
                #         logger.debug(msg="Adding pull-request comment {0} {1}".format([slug], comment[1:]))
                #         comment_writer.writerow([slug] + comment[1:])
            logger.info('Done processing %s.' % slug)

        log_writer.close()
        pr_writer.close()
        # comment_writer.close()

    @staticmethod
    def add_to_db(pr_f):
        # create a new session but don't init db tables
        SessionWrapper.load_config('orm/setup.yml')
        session = SessionWrapper.new(init=True)
        file_classifier = BasicFileTypeClassifier()

        old_prs = dict()
        logger.info(msg="Loading existing issues.... (it may take a while).")
        for prid in session.query(PullRequest.pr_id).all():
            old_prs[prid[0]] = True
        logger.info(msg="Pull requests already in the db: {0}".format(len(old_prs)))

        output_folder = os.path.abspath('./')
        pull_requests = CsvReader(os.path.join(output_folder, pr_f), mode='r')

        idx = 0
        logger.info("Importing new pull requests into the database.")
        for pr in pull_requests.readrows():
            if idx == 0:
                idx += 1
                continue  # skip header
            try:
                [slug,
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
                 commit_shas,
                 commit_files,
                 html_url] = pr

                if assignee_login == 'None' or assignee_login == '':
                    assignee_login = None
                if merged_by_login == 'None' or merged_by_login == '':
                    merged_by_login = None
                if closed_by_login == 'None' or closed_by_login == '':
                    closed_by_login = None

                if not int(pr_id) in old_prs:
                    gi = PullRequest(slug,
                                     int(issue_id),
                                     int(pr_id),
                                     int(pr_num),
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
                                     int(num_comments),
                                     int(num_review_comments),
                                     labels,
                                     int(num_commits),
                                     int(num_changed_files),
                                     int(num_additions),
                                     int(num_deletions),
                                     merge_sha,
                                     html_url)
                    logger.debug("Adding %s" % gi)
                    session.add(gi)
                    idx += 1

                    logger.debug("Adding commit shas for %s" % gi)
                    j = 1
                    for csha in commit_shas.split(','):
                        prci = PullRequestCommit(slug, int(pr_id), j, csha)
                        session.add(prci)
                        j += 1

                    logger.debug("Adding commit files for %s" % gi)
                    j = 1
                    for cf_cs in commit_files.split(','):
                        try:
                            cf, cs = cf_cs.split('_#_')
                            language = file_classifier.label_file(cf)
                            prci = PullRequestCommitFile(slug, int(pr_id), cs, cf, int(language))
                            session.add(prci)
                            j += 1
                        except ValueError:
                            pass

                    try:
                        session.commit()
                    except IntegrityError:
                        # this shouldn't happen, unless the dupe is in the file, not the db
                        logger.error("Duplicate entries found")
                        continue
            except Exception as e:
                traceback.print_exc(e)
                logger.error(pr, e)
                continue

        # session.commit()
        logger.info("New pull requests added to the database: %s" % str(idx - 1))

        # old_comments = dict()
        # logger.info(msg="Loading existing comments.... (it may take a while).")
        # for comment_id in session.query(Comment.comment_id).all():
        #     old_comments[comment_id[0]] = True
        # logger.info(msg="Comments already in the db: {0}".format(len(old_comments)))
        #
        # comments = CsvReader(os.path.join(output_folder, comments_f), mode='r')
        #
        # idx = 0
        # logger.info("Importing new comments into the database.")
        # for comment in comments.readrows():
        #     if idx == 0:
        #         idx += 1
        #         continue  # skip header
        #     try:
        #         [slug, issue_id, issue_number, comment_id, body, created_at, updated_at, user_login,
        #          user_github_id] = comment
        #         # FIXME clean up utf from body
        #         # does this work???
        #         body = bytes(body, 'utf-8').decode('utf-8', 'ignore')
        #
        #         if not int(comment_id) in old_comments:
        #             c = Comment(comment_id, slug, issue_id, issue_number, created_at, updated_at, user_github_id,
        #                              user_login, body)
        #             logger.debug("Adding issue comment %s." % c)
        #             session.add(c)
        #             session.commit()
        #             idx += 1
        #
        #         if not idx % 1000:
        #             try:
        #                 logger.info("Comments added so far: %s" % idx)
        #                 # session.commit()
        #             except IntegrityError:
        #                 # this shouldn't happen, unless the dupe is in the file, not the db
        #                 logger.error("Duplicate entry for comment %s" % comment_id)
        #                 continue
        #     except Exception as e:
        #         traceback.print_exc(e)
        #         logger.error(comment, e)
        #         continue
        #
        # session.commit()
        # logger.info("New comments added to the database: %s" % str(idx - 1))


def get_github_slugs(git_dir):
    dirs = [d for d in os.listdir(os.path.abspath(git_dir))]
    slugs = ['apache/' + d.strip() for d in dirs]
    return slugs


if __name__ == '__main__':
    pr_file = 'tmp_pullrequests.csv'
    # comment_file = 'tmp_comments.csv'
    into_db = False

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('pr_extractor')
    sys.stderr = open('error.log', mode='w')

    tokens = Tokens()
    tokens_iter = tokens.iterator()

    manager = Manager()

    tokens_queue = manager.Queue()
    for token in tokens_iter:
        tokens_queue.put(token)

    tokens_map = manager.dict()

    extractor = PrAndCommentExtractor(tokens, tokens_queue, tokens_map)
    logger.info("Retrieving GitHub project mirrors")
    slugs = get_github_slugs(sys.argv[1])
    logger.info("Beginning data extraction")
    extractor.start(slugs, pr_file)  # , comment_file)
    logger.info("Storing data into db")
    extractor.add_to_db(pr_file)  # , comment_file)
    logger.info("Done.")
