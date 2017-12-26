import logging
import os
import socket
import traceback
from multiprocessing import Manager, Pool
from multiprocessing import current_process

import requests
from _mysql_exceptions import IntegrityError
from github import Github
from github.GithubException import *

from apache_projects.orm.apache_tables import ApacheProject
from db import SessionWrapper
from pr_downloader.csv import CsvWriter, CsvReader
from pr_downloader.gh.api_tokens import Tokens
from pr_downloader.gh.extractor import BaseGitHubThreadedExtractor
from pr_downloader.orm.github_tables import PullRequest, Comment


class PrAndCommentExtractor(BaseGitHubThreadedExtractor):
    @staticmethod
    def parse_issue(pid, g, issue):
        metadata = None
        pull_request = issue.pull_request  # IssuePullRequest
        if pull_request is not None:
            pr_html_url = pull_request.html_url
            pr_num = pr_html_url.split('/')[-1]

            issue_id = issue.id
            issue_number = issue.number
            state = issue.state
            created_at = str(issue.created_at)
            closed_at = str(issue.closed_at)

            created_by = issue.user
            created_by_login = None
            if created_by is not None:
                created_by_login = created_by.login

            closed_by = issue.closed_by
            closed_by_login = None
            if closed_by is not None:
                closed_by_login = closed_by.login

            assignee = issue.assignee
            assignee_login = None
            if assignee is not None:
                assignee_login = assignee.login

            title = issue.title.strip().replace("\n", "").replace("\r", "")
            num_comments = issue.comments  # int
            labels = ','.join([l.name for l in issue.labels])  # [Label]

            metadata = [issue_id,
                        issue_number,
                        state,
                        created_at,
                        closed_at,
                        created_by_login,
                        closed_by_login,
                        assignee_login,
                        title,
                        num_comments,
                        labels,
                        pr_num]

            PrAndCommentExtractor.wait_if_depleted(pid, g)

        return metadata

    @staticmethod
    def parse_comments(pid, g, slug, issue):
        comments = list()

        comments_pglist = issue.get_comments()
        for comment in comments_pglist:
            comment_id = comment.id
            body = comment.body.strip()
            created_at = comment.created_at
            updated_at = comment.updated_at
            user_login = comment.user.login
            user_gh_id = comment.user.id
            comments.append(
                [slug, issue.id, issue.number, comment_id, body, created_at, updated_at, user_login, user_gh_id])

        if issue.pull_request is not None:  # is an actual issue:  # is a PR
            pr = issue.repository.get_pull(issue.number)
            comments_pglist = pr.get_review_comments()
            for comment in comments_pglist:
                comment_id = comment.id
                created_at = comment.created_at
                updated_at = comment.updated_at
                body = comment.body.strip()
                user_login = comment.user.login
                user_gh_id = comment.user.id
                comments.append(
                    [slug, pr.id, pr.number, comment_id, body, created_at, updated_at, user_login, user_gh_id])

        PrAndCommentExtractor.wait_if_depleted(pid, g)
        return comments

    def fetch_issues_comments(self, slug):
        pid = current_process().pid
        issues = list()
        comments = list()

        if slug in self.seen:
            logging.info('[pid: {0}] Skipping {1}'.format(pid, slug))
            return slug, pid, None, issues, comments, 'Skipped'
        else:
            self.seen.add(slug)

        logger.info('[pid: {0}] Processing {1}'.format(pid, slug))

        try:
            _token = self.tokens_map[pid]
            g = Github(_token)
            # check rate limit before starting
            PrAndCommentExtractor.wait_if_depleted(pid, g)
            logger.info(msg="[pid: %s] Process not depleted, keep going." % pid)
            repo = g.get_repo(slug)

            if repo and repo.has_issues:
                for issue in repo.get_issues(state=u'closed'):
                    try:
                        logger.info(
                            msg='[pid: {0}] Fetching closed issue/pull-request {1} from {2}'.format(pid, issue.number,
                                                                                                    slug))
                        metadata_issue = PrAndCommentExtractor.parse_issue(pid, g, issue)
                        if metadata_issue:
                            issues.append(metadata_issue)

                            metadata_comments = PrAndCommentExtractor.parse_comments(pid, g, slug, issue)
                            if metadata_comments:
                                comments.append(metadata_comments)
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
                            msg='[pid: {0}] Fetching open issue/pull-request {1} from {2}'.format(pid, issue.number,
                                                                                                  slug))
                        metadata = PrAndCommentExtractor.parse_issue(pid, g, issue)
                        issues.append(metadata)

                        metadata = PrAndCommentExtractor.parse_comments(pid, g, slug, issue)
                        if metadata:
                            comments.append(metadata)
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
            return slug, pid, None, issues, comments, "%s seems to be private" % slug
        except UnknownObjectException:
            logger.warning("Repository %s cannot be found (raised 404 error)" % slug)
            return slug, pid, None, issues, comments, "%s not found" % slug
        except GithubException as ghe:
            logger.warning("Unknown error for repository %s" % slug)
            return slug, pid, None, issues, comments, str(ghe).strip().replace("\n", " ").replace("\r", " ")
        except Exception as e:
            traceback.print_exc(e)
            return slug, pid, None, issues, comments, str(e).strip().replace("\n", " ").replace("\r", " ")

        logger.debug((_token, PrAndCommentExtractor.get_rate_limit(g)))
        return slug, pid, _token, issues, comments, None

    def start(self, projects, issues_f, comments_f):
        # create a new session and init db tables
        SessionWrapper.load_config('orm/setup.yml')
        session = SessionWrapper.new(init=False)
        for issue in session.query(PullRequest.slug).distinct():
            # self.seen[issue] = True
            self.seen.add(issue)
        logger.info(msg="DB projects with issues: {0}".format(len(self.seen)))

        output_folder = os.path.abspath('./')
        log_writer = CsvWriter(os.path.join(output_folder, 'extracted-issues-error.log'), 'a')

        header = None
        f = os.path.join(output_folder, issues_f)
        if not os.path.exists(f):
            header = ['slug', 'issue_id', 'issue_number', 'state', 'created_at',
                      'closed_at', 'created_by_login', 'closed_by_login', 'assignee_login', 'title', 'num_comments',
                      'labels', 'pr_num']
        issue_writer = CsvWriter(f, 'w')
        if header:
            issue_writer.writerow(header)
        logger.debug("Opened issues file %s" % issues_f)

        header = None
        f = os.path.join(output_folder, comments_f)
        if not os.path.exists(f):
            header = ['slug', 'issue_id', 'issue_number', 'comment_id', 'body', 'created_at', 'updated_at',
                      'user_login', 'user_github_id']
        comment_writer = CsvWriter(f, 'w')
        if header:
            comment_writer.writerow(header)
        logger.debug("Opened comments file %s" % comments_f)

        self.initialize()
        pool = Pool(processes=self.tokens.length(), initializer=self.initialize, initargs=())

        # projects = ["bateman/dynkaas", "bateman/filebotology", "fujimura/git-gsub", "rbrito/tunesviewer"]

        for result in pool.imap_unordered(self.fetch_issues_comments, projects):
            (slug, pid, _token, issues, comments_list, error) = result
            if error is not None:
                logging.error(msg=[slug, error])
                log_writer.writerow([slug, error])
            elif comments_list:
                logger.info("Saving issues to temp file")
                for issue in issues:
                    logger.debug(msg="Adding issue {0} {1}".format([slug], issue))
                    issue_writer.writerow([slug] + issue)
                logger.info("Saving comments to temp file")
                for comments in comments_list:
                    for comment in comments:
                        logger.debug(msg="Adding issue/pull-request comment {0} {1}".format([slug], comment[1:]))
                        comment_writer.writerow([slug] + comment[1:])
            logger.info('Done processing %s.' % slug)

        log_writer.close()
        issue_writer.close()
        comment_writer.close()

    @staticmethod
    def add_to_db(issue_f, comments_f):
        # create a new session but don't init db tables
        SessionWrapper.load_config('orm/setup.yml')
        session = SessionWrapper.new(init=False)

        old_issues = dict()
        logger.info(msg="Loading existing issues.... (it may take a while).")
        for issue_id in session.query(PullRequest.issue_id):
            old_issues[issue_id[0]] = True
        logger.info(msg="Issues already in the db: {0}".format(len(old_issues)))

        output_folder = os.path.abspath('./')
        issues = CsvReader(os.path.join(output_folder, issue_f), mode='r')

        idx = 0
        logger.info("Importing new issues into the database.")
        for issue in issues.readrows():
            if idx == 0:
                idx += 1
                continue  # skip header
            try:
                [slug, issue_id, issue_number, state, created_at, closed_at,
                 created_by_login, closed_by_login, assignee_login, title,
                 num_comments, labels, pr_num] = issue

                if assignee_login == 'None' or assignee_login == '':
                    assignee_login = None
                if pr_num == 'None' or pr_num == '':
                    pr_num = None

                if not int(issue_id) in old_issues:
                    gi = PullRequest(slug, int(issue_id), issue_number, state,
                                     created_at, closed_at, created_by_login,
                                     closed_by_login, assignee_login, title,
                                     num_comments, labels, pr_num)
                    logger.debug("Adding issue %s." % gi)
                    session.add(gi)
                    idx += 1

                if not idx % 1000:
                    try:
                        logger.info("Issues added so far: %s" % idx)
                        session.commit()
                    except IntegrityError:
                        # this shouldn't happen, unless the dupe is in the file, not the db
                        logger.error("Duplicate entry for comment %s" % issue_id)
                        continue
            except Exception as e:
                traceback.print_exc(e)
                logger.error(issue, e)
                continue

        session.commit()
        logger.info("New issues added to the database: %s" % str(idx - 1))

        old_comments = dict()
        logger.info(msg="Loading existing comments.... (it may take a while).")
        for comment_id in session.query(Comment.comment_id).all():
            old_comments[comment_id[0]] = True
        logger.info(msg="Comments already in the db: {0}".format(len(old_comments)))

        comments = CsvReader(os.path.join(output_folder, comments_f), mode='r')

        idx = 0
        logger.info("Importing new comments into the database.")
        for comment in comments.readrows():
            if idx == 0:
                idx += 1
                continue  # skip header
            try:
                [slug, issue_id, issue_number, comment_id, body, created_at, updated_at, user_login,
                 user_github_id] = comment
                # FIXME clean up utf from body
                # does this work???
                body = bytes(body, 'utf-8').decode('utf-8', 'ignore')

                if not int(comment_id) in old_comments:
                    c = Comment(comment_id, slug, issue_id, issue_number, created_at, updated_at, user_github_id,
                                     user_login, body)
                    logger.debug("Adding issue comment %s." % c)
                    session.add(c)
                    session.commit()
                    idx += 1

                if not idx % 1000:
                    try:
                        logger.info("Comments added so far: %s" % idx)
                        # session.commit()
                    except IntegrityError:
                        # this shouldn't happen, unless the dupe is in the file, not the db
                        logger.error("Duplicate entry for comment %s" % comment_id)
                        continue
            except Exception as e:
                traceback.print_exc(e)
                logger.error(comment, e)
                continue

        session.commit()
        logger.info("New comments added to the database: %s" % str(idx - 1))


def exclude_malformed(slugs):
    malformed_url = list()
    for slug in slugs:
        request = requests.get('https://github.com/' + slug)
        if request.status_code != 200:
            malformed_url.append(slug)
    return malformed_url


def get_github_slugs():
    SessionWrapper.load_config('../apache_crawler/orm/cfg/setup.yml')
    session = SessionWrapper.new(init=False)

    slugs = session.query(ApacheProject.name).filter_by(repository_type='git').all()
    slugs = ['apache/' + n[0].strip() for n in slugs]
    malformed_slugs = exclude_malformed(slugs)
    slugs = [m for m in slugs if m not in malformed_slugs]
    return slugs


if __name__ == '__main__':
    pr_file = 'tmp_pullrequests.csv'
    comment_file = 'tmp_comments.csv'
    into_db = False

    logging.basicConfig()
    logger = logging.getLogger('pr_extractor')
    logger.setLevel(logging.DEBUG)

    tokens = Tokens()
    tokens_iter = tokens.iterator()

    manager = Manager()

    tokens_queue = manager.Queue()
    for token in tokens_iter:
        tokens_queue.put(token)

    tokens_map = manager.dict()

    extractor = PrAndCommentExtractor(tokens, tokens_queue, tokens_map)
    logger.info("Beginning data extraction.")
    slugs = get_github_slugs()
    extractor.start(slugs, pr_file, comment_file)
    logger.info("Beginning data import into db.")
    extractor.add_to_db(pr_file, comment_file)
    logger.info("Done.")
