import logging
import os

import pygit2
from git import Repo

log = logging.getLogger('RepoCloner')


def slug_to_folder_name(slug):
    if slug is None:
        return None
    return '_____'.join(slug.split('/'))


class RepoCloner:

    @staticmethod
    def clone(slug, repos_folder, url):
        try:
            path = os.path.join(repos_folder, slug_to_folder_name(slug))

            log.info(msg='Cloning repo {0} into {1}.'.format(slug, path))
            pygit2.clone_repository(url=url, path=path)
        except Exception as e:
            log.error('Error cloning repo {0}: {1}'.format(slug, e))

    @staticmethod
    def update_submodules(repos_folder):
        try:
            path = os.path.join(repos_folder, '.git')

            log.info(msg='Updating submodules of repo at {0}.'.format(path))
            repo = pygit2.Repository(path=path)
            repo.update_submodules()
        except Exception as e:
            log.error('Error updating submodules at {0}'.format(e))

    @staticmethod
    def pull(dest):
        try:
            repo = Repo(path=dest)
            o = repo.remotes.origin
            o.pull()
        except Exception as e:
            log.error('Error pulling git repo at {0}'.format(e))
