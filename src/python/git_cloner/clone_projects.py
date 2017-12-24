import logging
import os

from git_cloner.cloner import RepoCloner
from git_cloner.cloner import slug_to_folder_name
from orm.apache_tables import ApacheProject
from orm.setup import SessionWrapper


def start(projects, destination_dir='./apache_repos'):
    log.info("Starting project cloning.")

    for slug in projects:
        slug = slug.strip()
        s2f = slug_to_folder_name(slug)
        dest = os.path.join(destination_dir, s2f)

        if os.path.exists(dest):
            log.info(
                'Project {0} already available locally in {1}, performing an update.'.format(slug, dest))
            try:
                RepoCloner.pull(dest)
                RepoCloner.update_submodules(dest)
            except:
                log.error("Error updating git repo in folder %s" % dest)
        else:
            try:
                RepoCloner.clone(slug, destination_dir)
                log.info('Project repository {0} cloned into {1}'.format(slug, s2f))
                RepoCloner.update_submodules(dest)
            except:
                log.error('Error cloning repo {0} into {1}'.format(slug, s2f))

    log.info('Done.')


def get_projects():
    SessionWrapper.load_config('../apache_crawler/orm/cfg/setup.yml')
    session = SessionWrapper.new(init=False)

    projects = session.query(ApacheProject.name).filter_by(repository_type='git').all()
    return projects


if __name__ == '__main__':
    logging.basicConfig()
    log = logging.getLogger('git_cloner')
    log.setLevel(logging.DEBUG)

    git_projects = get_projects()
    start(git_projects)
