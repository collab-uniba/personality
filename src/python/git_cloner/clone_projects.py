import logging
import os

from git_cloner.cloner import RepoCloner
from apache_projects.orm.apache_tables import ApacheProject
from db.setup import SessionWrapper


def start(projects, destination_dir='./apache_repos'):
    log.info("Starting project cloning")

    for slug, url in projects:
        slug = slug.strip()
        log.info('Processing %s' % slug)
        dest = os.path.join(destination_dir, slug)

        if os.path.exists(dest):
            log.info(
                'Project {0} already available locally in {1}, performing an update.'.format(slug, dest))
            try:
                RepoCloner.pull(dest)
            except:
                log.error("Error updating git repo in folder %s" % dest)
        else:
            try:
                RepoCloner.clone(slug, destination_dir, url)
                log.info('Project repository {0} cloned into {1}'.format(slug, slug))
            except:
                log.error('Error cloning repo {0} into {1}'.format(slug, slug))

    log.info('Done')


def get_projects():
    SessionWrapper.load_config('../db/cfg/setup.yml')
    session = SessionWrapper.new(init=False)

    projects = session.query(ApacheProject.name, ApacheProject.repository_url).filter_by(repository_type='git').all()
    return projects


if __name__ == '__main__':
    logging.basicConfig()
    log = logging.getLogger('git_cloner')
    log.setLevel(logging.DEBUG)

    git_projects = get_projects()
    start(git_projects)
